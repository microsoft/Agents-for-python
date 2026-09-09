# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Shared artifact, dependency and process utilities."""

import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

DEPENDENCY = "microsoft-teams-api"
PACKAGE = "microsoft-agents-hosting-msteams"
ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = ROOT / "libraries" / PACKAGE
SOURCE_ROOT = PACKAGE_ROOT / "microsoft_agents/hosting/msteams"
ARTIFACTS = ROOT / "artifacts/teams-api-drift"
MANIFEST = PACKAGE_ROOT / "teams-api-usage-manifest.json"
CAPABILITIES = PACKAGE_ROOT / "config/teams-capabilities.yaml"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    write_text(
        path, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def destination(path, name):
    path = Path(path)
    return path if path.suffix == Path(name).suffix else path / name


def validate_artifact(data, collection=None, dependency=DEPENDENCY):
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("Expected a schemaVersion 1 artifact")
    if data.get("dependency") != dependency:
        raise ValueError(f"Expected dependency {dependency}")
    if collection and not isinstance(data.get(collection), list):
        raise ValueError(f"Artifact must include a {collection} array")
    return data


def declared_requirement(source):
    """Read literal install_requires entries without executing setup.py."""
    matches = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id == "setup"
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "setup"
        ):
            continue
        for keyword in node.keywords:
            if keyword.arg != "install_requires":
                continue
            if not isinstance(keyword.value, (ast.List, ast.Tuple)):
                raise ValueError("install_requires must be a literal list")
            for entry in keyword.value.elts:
                if isinstance(entry, ast.Constant) and isinstance(entry.value, str):
                    requirement = Requirement(entry.value)
                    if canonicalize_name(requirement.name) == DEPENDENCY:
                        matches.append(requirement)
    if len(matches) != 1 or matches[0].url or matches[0].marker:
        raise ValueError("Expected one unconditional Teams API version requirement")
    return matches[0]


def declared_minimum(requirement):
    candidates = [
        Version(s.version)
        for s in requirement.specifier
        if s.operator in ("==", ">=", "~=") and "*" not in s.version
    ]
    candidates = [
        v for v in candidates if requirement.specifier.contains(v, prereleases=True)
    ]
    if not candidates:
        raise ValueError(
            "Teams API requirement needs an inclusive minimum or exact version"
        )
    return str(max(candidates))


def latest_stable(metadata=None):
    if metadata is None:
        with urlopen(
            f"https://pypi.org/pypi/{DEPENDENCY}/json", timeout=60
        ) as response:
            metadata = json.load(response)
    versions = []
    for value, files in metadata["releases"].items():
        version = Version(value)
        if (
            not version.is_prerelease
            and not version.is_devrelease
            and any(not file.get("yanked", False) for file in files)
        ):
            versions.append(version)
    if not versions:
        raise ValueError("No non-yanked stable Teams API release found")
    return str(max(versions))


def python_in(directory):
    path = Path(directory).resolve() / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    return (
        Path("\\\\?\\" + str(path))
        if os.name == "nt" and not str(path).startswith("\\\\?\\")
        else path
    )


def temporary_environment(prefix):
    # Extended paths are necessary for Graph's generated module filenames on
    # Windows. Keep creation and TemporaryDirectory cleanup on the same root.
    root = str(Path(tempfile.gettempdir()).resolve())
    if os.name == "nt" and not root.startswith("\\\\?\\"):
        root = "\\\\?\\" + root
    return tempfile.TemporaryDirectory(prefix=prefix, dir=root)


def run(args, *, cwd=ROOT, env=None):
    result = subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=1800,
    )
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(map(str, args))}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout
