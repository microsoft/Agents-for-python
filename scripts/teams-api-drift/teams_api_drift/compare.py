# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Extract exact upstream releases and compare normalized public contracts."""

import difflib
import json
import os
from pathlib import Path
import sys

from packaging.version import Version

from .common import (
    DEPENDENCY,
    destination,
    latest_stable,
    python_in,
    read_json,
    run,
    temporary_environment,
    validate_artifact,
    write_json,
    write_text,
)


def install_version(directory, version):
    version = str(Version(version))
    # ensurepip cannot bootstrap from an extended-length executable path on
    # Windows. Create using the ordinary short environment path, then use the
    # extended path for pip installs and subsequent generated Graph imports.
    create_path = (
        str(directory).removeprefix("\\\\?\\") if os.name == "nt" else directory
    )
    run([os.environ.get("TEAMS_API_PYTHON", sys.executable), "-m", "venv", create_path])
    python = python_in(directory)
    run(
        [
            python,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"{DEPENDENCY}=={version}",
            "packaging==25.0",
        ]
    )
    return python


def extract_version(python, output, version):
    run(
        [python, "-m", "teams_api_drift.extract", output],
        cwd=Path(__file__).resolve().parents[1],
    )
    model = validate_artifact(read_json(output), "symbols")
    if Version(model["version"]) != Version(version) or not model["symbols"]:
        raise ValueError(
            f"Extractor did not produce the requested API version {version}"
        )
    return model


def signature_compatibility(before, after):
    """Recognize added optional arguments/overloads without requiring adaptation."""

    def accepts_old_calls(old, new):
        if old.get("returnType") != new.get("returnType") or old.get(
            "async"
        ) != new.get("async"):
            return False
        old_params, new_params = old["parameters"], new["parameters"]
        if len(new_params) < len(old_params):
            return False
        for previous, current in zip(old_params, new_params):
            if any(
                previous.get(key) != current.get(key)
                for key in ("name", "kind", "type", "default")
            ):
                return False
            if previous.get("optional") and not current.get("optional"):
                return False
        return all(
            p.get("optional") or p.get("kind") in ("VAR_POSITIONAL", "VAR_KEYWORD")
            for p in new_params[len(old_params) :]
        )

    if all(any(accepts_old_calls(old, new) for new in after) for old in before):
        return "non-breaking"
    return "potentially-breaking"


def compare_models(before, after):
    for model in (before, after):
        validate_artifact(model, "symbols")
        if not model["symbols"]:
            raise ValueError("Cannot compare an empty API model")
    changes = []

    def add(
        kind,
        symbol,
        member=None,
        old=None,
        new=None,
        compatibility="potentially-breaking",
    ):
        changes.append(
            {
                "kind": kind,
                "symbol": symbol,
                "member": member,
                "before": old,
                "after": new,
                "compatibility": compatibility,
                "evidence": ["normalized-api-model"],
            }
        )

    old_symbols = {symbol["name"]: symbol for symbol in before["symbols"]}
    new_symbols = {symbol["name"]: symbol for symbol in after["symbols"]}
    for name in sorted(old_symbols.keys() | new_symbols.keys()):
        old, new = old_symbols.get(name), new_symbols.get(name)
        if old is None or new is None:
            add(
                "symbol-added" if old is None else "symbol-removed",
                name,
                old=old,
                new=new,
                compatibility="non-breaking" if old is None else "breaking",
            )
            continue
        for field, kind in (
            ("exportPaths", "export-path-changed"),
            ("kind", "symbol-kind-changed"),
            ("type", "type-alias-changed"),
            ("value", "value-changed"),
            ("modelConfig", "model-config-changed"),
            ("deprecated", "deprecation-changed"),
        ):
            if old.get(field) != new.get(field):
                add(kind, name, old=old.get(field), new=new.get(field))
        for member in sorted(old["properties"].keys() | new["properties"].keys()):
            old_field, new_field = old["properties"].get(member), new["properties"].get(
                member
            )
            if old_field is None or new_field is None:
                add(
                    "property-added" if old_field is None else "property-removed",
                    name,
                    member,
                    old_field,
                    new_field,
                    (
                        "breaking"
                        if new_field is None or not new_field["optional"]
                        else "non-breaking"
                    ),
                )
                continue
            for field in sorted(old_field.keys() | new_field.keys()):
                if old_field.get(field) == new_field.get(field):
                    continue
                kind = {
                    "optional": "requiredness",
                    "validationAlias": "validation-alias",
                    "serializationAlias": "serialization-alias",
                }.get(field, field)
                add(
                    f"property-{kind}-changed",
                    name,
                    member,
                    old_field.get(field),
                    new_field.get(field),
                )
        for member in sorted(old["methods"].keys() | new["methods"].keys()):
            old_method, new_method = old["methods"].get(member), new["methods"].get(
                member
            )
            kind = (
                "method-added"
                if old_method is None
                else (
                    "method-removed"
                    if new_method is None
                    else "method-signature-changed"
                )
            )
            if old_method != new_method:
                add(
                    kind,
                    name,
                    member,
                    old_method,
                    new_method,
                    (
                        "non-breaking"
                        if old_method is None
                        else (
                            "breaking"
                            if new_method is None
                            else signature_compatibility(old_method, new_method)
                        )
                    ),
                )
        if old["constructors"] != new["constructors"]:
            add(
                "constructor-changed",
                name,
                "__init__",
                old["constructors"],
                new["constructors"],
                signature_compatibility(old["constructors"], new["constructors"]),
            )
        for member in sorted(old["enumMembers"].keys() | new["enumMembers"].keys()):
            if member not in old["enumMembers"]:
                add(
                    "enum-member-added",
                    name,
                    member,
                    new=new["enumMembers"][member],
                    compatibility="non-breaking",
                )
            elif member not in new["enumMembers"]:
                add(
                    "enum-member-removed",
                    name,
                    member,
                    old=old["enumMembers"][member],
                    compatibility="breaking",
                )
            elif old["enumMembers"][member] != new["enumMembers"][member]:
                add(
                    "enum-value-changed",
                    name,
                    member,
                    old["enumMembers"][member],
                    new["enumMembers"][member],
                )
    changes.sort(
        key=lambda change: (change["symbol"], change["member"] or "", change["kind"])
    )
    for index, change in enumerate(changes, 1):
        change["id"] = f"TSAPI-{index:04d}"
    old_text = json.dumps(before["symbols"], indent=2, sort_keys=True) + "\n"
    new_text = json.dumps(after["symbols"], indent=2, sort_keys=True) + "\n"
    diff = "".join(
        difflib.unified_diff(
            old_text.splitlines(True),
            new_text.splitlines(True),
            fromfile="baseline-api.json",
            tofile="candidate-api.json",
        )
    )
    return {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "fromVersion": before["version"],
        "toVersion": after["version"],
        "changed": bool(changes),
        "changes": changes,
        "diff": diff,
        "addedLines": [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ],
        "removedLines": [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ],
        "baselineSymbols": before["symbols"],
        "candidateSymbols": after["symbols"],
        "extractorVersion": before.get("extractorVersion"),
    }


def compare_versions(from_version, to_version, output, work_root=None):
    """The caller can retain work_root to run contracts in its candidate environment."""
    to_version = to_version or latest_stable()
    target = destination(output, "raw-api-diff.json").resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    def perform(work):
        models = []
        for label, version in (("baseline", from_version), ("candidate", to_version)):
            python = install_version(Path(work) / label, version)
            models.append(
                extract_version(python, target.parent / f"{label}-api.json", version)
            )
        comparison = compare_models(*models)
        write_json(target, comparison)
        write_text(target.parent / "teams-api.diff", comparison["diff"])
        return comparison

    if work_root is not None:
        return perform(work_root)
    with temporary_environment(prefix="teams-api-drift-") as work:
        return perform(work)
