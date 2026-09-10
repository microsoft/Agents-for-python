# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Validate Teams API usage and capability metadata against extension source."""

import ast
from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path
import subprocess

import yaml

from .common import (
    CAPABILITIES,
    DEPENDENCY,
    MANIFEST,
    PACKAGE_ROOT,
    ROOT,
    declared_requirement,
)

SOURCE_REVIEW_GUIDE = "scripts/teams-api-drift/README.md#source-review-acknowledgments"
USAGE_REVIEW_OUTCOME = "no-usage-metadata-change"
CAPABILITY_REVIEW_OUTCOME = "no-capability-metadata-change"


@dataclass(frozen=True)
class TeamsImport:
    symbol: str
    file: str
    line: int


def _run_git(root, *args, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode:
        raise ValueError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout if result.returncode == 0 else None


def _git_files(root, *args):
    value = _run_git(root, *args) or ""
    return {item.replace("\\", "/") for item in value.split("\0") if item}


def _git_file(root, revision, file):
    return _run_git(root, "show", f"{revision}:{file}", check=False)


def _imports_from_text(file, text):
    imports = []
    for node in ast.walk(ast.parse(text, filename=file)):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("microsoft_teams.api")
        ):
            for name in node.names:
                imports.append(
                    TeamsImport(f"{node.module}.{name.name}", file, node.lineno)
                )
        elif isinstance(node, ast.Import):
            for name in node.names:
                if name.name.startswith("microsoft_teams.api"):
                    imports.append(TeamsImport(name.name, file, node.lineno))
    return imports


def _source_files(package_root, source_root):
    return sorted(
        file.relative_to(package_root).as_posix() for file in source_root.rglob("*.py")
    )


def _collect_imports(package_root, files):
    return [
        imported
        for file in files
        for imported in _imports_from_text(
            file, (package_root / file).read_text(encoding="utf-8")
        )
    ]


def _annotation_symbol(node, aliases):
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Subscript):
        return _annotation_symbol(node.slice, aliases)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _annotation_symbol(node.left, aliases) or _annotation_symbol(
            node.right, aliases
        )
    return None


class _UsageVisitor(ast.NodeVisitor):
    def __init__(self, aliases):
        self.aliases = aliases
        self.variables = {}
        self.members = []
        self.public_types = set()
        self.public_class_depth = 0

    def visit_ClassDef(self, node):
        public = not node.name.startswith("_")
        if public:
            self.public_class_depth += 1
        self.generic_visit(node)
        if public:
            self.public_class_depth -= 1

    def visit_FunctionDef(self, node):
        previous = self.variables.copy()
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        if node.args.vararg:
            arguments.append(node.args.vararg)
        if node.args.kwarg:
            arguments.append(node.args.kwarg)
        for argument in arguments:
            symbol = _annotation_symbol(argument.annotation, self.aliases)
            if symbol:
                self.variables[argument.arg] = symbol
                if self.public_class_depth or not node.name.startswith("_"):
                    self.public_types.add(symbol)
        return_symbol = _annotation_symbol(node.returns, self.aliases)
        if return_symbol and (self.public_class_depth or not node.name.startswith("_")):
            self.public_types.add(return_symbol)
        self.generic_visit(node)
        self.variables = previous

    visit_AsyncFunctionDef = visit_FunctionDef

    def _value_symbol(self, value):
        if not isinstance(value, ast.Call):
            return None
        if isinstance(value.func, ast.Name):
            return self.aliases.get(value.func.id)
        if (
            isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.attr in ("model_validate", "parse_obj")
        ):
            return self.aliases.get(value.func.value.id)
        return None

    def visit_Assign(self, node):
        symbol = self._value_symbol(node.value)
        if symbol:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variables[target.id] = symbol
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        symbol = _annotation_symbol(
            node.annotation, self.aliases
        ) or self._value_symbol(node.value)
        if symbol and isinstance(node.target, ast.Name):
            self.variables[node.target.id] = symbol
        self.generic_visit(node)

    def visit_Attribute(self, node):
        segments = [node.attr]
        root = node.value
        while isinstance(root, ast.Attribute):
            segments.insert(0, root.attr)
            root = root.value
        if isinstance(root, ast.Name):
            symbol = self.variables.get(root.id) or self.aliases.get(root.id)
            if symbol:
                parent = getattr(node, "_teams_parent", None)
                kind = (
                    "method"
                    if isinstance(parent, ast.Call) and parent.func is node
                    else "write" if isinstance(node.ctx, ast.Store) else "read"
                )
                self.members.append((symbol, ".".join(segments), kind, node.lineno))
        self.generic_visit(node)


def _static_usage(file, text):
    tree = ast.parse(text, filename=file)
    aliases = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._teams_parent = node
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("microsoft_teams.api")
        ):
            for name in node.names:
                aliases[name.asname or name.name] = f"{node.module}.{name.name}"
    visitor = _UsageVisitor(aliases)
    visitor.visit(tree)
    return visitor.members, visitor.public_types


def _validate_static_usage(package_root, files, manifest, errors):
    for file in files:
        members, public_types = _static_usage(
            file, (package_root / file).read_text(encoding="utf-8")
        )
        usages = [
            usage for usage in manifest["usages"] if file in usage.get("files", [])
        ]
        for symbol in public_types:
            matching = [
                usage for usage in usages if usage.get("upstreamSymbol") == symbol
            ]
            if matching and not any(
                usage.get("exposure") in ("publicly-exposed", "re-exported")
                for usage in matching
            ):
                errors.append(
                    f"{symbol} appears in a public annotation in {file} but is not "
                    "marked publicly exposed"
                )
        reported = set()
        for symbol, member, kind, line in members:
            matching = [
                usage for usage in usages if usage.get("upstreamSymbol") == symbol
            ]
            if not matching:
                continue
            field = {
                "method": "methodsCalled",
                "write": "propertiesWritten",
                "read": "propertiesRead",
            }[kind]
            declared = {value for usage in matching for value in usage.get(field, [])}
            covered = any(
                value == member
                or value.replace("[]", "").split(".")[0] == member.split(".")[0]
                for value in declared
            )
            key = (symbol, member, kind)
            if not covered and key not in reported:
                reported.add(key)
                action = {"method": "called", "write": "written", "read": "read"}[kind]
                errors.append(
                    f"{symbol}.{member} is statically {action} in {file}:{line} but "
                    f"is absent from {field}"
                )


def _matches_owner(owner, file):
    owner = owner.replace("\\", "/").rstrip("/")
    file = file.replace("\\", "/")
    if "*" in owner:
        return fnmatch.fnmatchcase(file, owner)
    return file == owner or file.startswith(owner + "/")


def _owners_for(document, file):
    return sorted(
        name
        for name, capability in document.get("capabilities", {}).items()
        if any(_matches_owner(owner, file) for owner in capability.get("owners", []))
    )


def _owner_patterns_for(document, file):
    return sorted(
        owner
        for capability in document.get("capabilities", {}).values()
        for owner in capability.get("owners", [])
        if _matches_owner(owner, file)
    )


def _upstream_areas(symbol):
    if symbol == "microsoft_teams.api.ApiClient":
        return ["microsoft_teams.api.clients"]
    exact = {
        "microsoft_teams.api.models.channel_data.ChannelInfo": (
            "microsoft_teams.api.models.channel_data.channel_info"
        ),
        "microsoft_teams.api.models.channel_data.TeamInfo": (
            "microsoft_teams.api.models.channel_data.team_info"
        ),
    }
    if symbol in exact:
        return [exact[symbol]]
    prefixes = {
        "microsoft_teams.api.models.ChannelData": "models.channel_data",
        "microsoft_teams.api.models.ChannelInfo": "models.channel_data.channel_info",
        "microsoft_teams.api.models.TeamInfo": "models.channel_data.team_info",
        "microsoft_teams.api.models.NotificationInfo": "models.channel_data",
        "microsoft_teams.api.models.FeedbackLoop": "models.channel_data",
        "microsoft_teams.api.models.MeetingInfo": "models.meetings",
        "microsoft_teams.api.models.FileConsent": "models.file",
        "microsoft_teams.api.models.MessagingExtension": "models.messaging_extension",
        "microsoft_teams.api.models.TaskModule": "models.task_module",
        "microsoft_teams.api.models.AppBasedLinkQuery": "models.app_based_link_query",
    }
    for prefix, area in prefixes.items():
        if symbol.startswith(prefix):
            return [f"microsoft_teams.api.{area}"]
    module = symbol.rsplit(".", 1)[0]
    return [module] if module != "microsoft_teams.api" else []


def _valid_review(review, outcome):
    return (
        isinstance(review, dict)
        and review.get("outcome") == outcome
        and isinstance(review.get("reason"), str)
        and bool(review["reason"].strip())
    )


def _review_changed(before, after, outcome):
    return before != after and _valid_review(after, outcome)


def _latest_commit(root, base, files):
    if not files:
        return None
    value = _run_git(root, "log", "-1", "--format=%H", f"{base}..HEAD", "--", *files)
    return value.strip() or None


def _metadata_is_fresh(root, base, working, source_files, metadata_file):
    if any(file in working for file in source_files):
        return metadata_file in working
    if metadata_file in working:
        return True
    source_commit = _latest_commit(root, base, source_files)
    metadata_commit = _latest_commit(root, base, [metadata_file])
    if not source_commit or not metadata_commit:
        return False
    return (
        source_commit == metadata_commit
        or _run_git(
            root,
            "merge-base",
            "--is-ancestor",
            source_commit,
            metadata_commit,
            check=False,
        )
        is not None
    )


def _read_base_document(root, base, file, loader):
    text = _git_file(root, base, file)
    if text is None:
        return None
    try:
        return loader(text)
    except (ValueError, yaml.YAMLError):
        return None


def _capability_change_addressed(change, before, after):
    file = change["file"]
    if not change["baseExists"] and change["currentExists"]:
        return any(
            pattern not in _owner_patterns_for(before, file)
            for pattern in _owner_patterns_for(after, file)
        )
    if change["baseExists"] and not change["currentExists"]:
        return any(
            pattern not in _owner_patterns_for(after, file)
            for pattern in _owner_patterns_for(before, file)
        )
    if change["baseOwners"] != change["currentOwners"]:
        return True
    if not change["importChanged"]:
        return False
    return any(
        before.get("capabilities", {}).get(name, {}).get("owners")
        != after.get("capabilities", {}).get(name, {}).get("owners")
        or before.get("capabilities", {}).get(name, {}).get("upstreamAreas")
        != after.get("capabilities", {}).get(name, {}).get("upstreamAreas")
        for name in set(change["baseOwners"] + change["currentOwners"])
    )


def _validate_change_reviews(
    root,
    package_root,
    base_ref,
    manifest,
    capabilities,
    current_imports,
    errors,
    manifest_path,
    capabilities_path,
):
    base = (_run_git(root, "merge-base", "HEAD", base_ref, check=False) or "").strip()
    if not base:
        raise ValueError(f"Unable to resolve Git base ref {base_ref}")
    package_path = package_root.relative_to(root).as_posix()
    manifest_file = manifest_path.relative_to(root).as_posix()
    capabilities_file = capabilities_path.relative_to(root).as_posix()
    base_manifest = _read_base_document(root, base, manifest_file, json.loads)
    base_capabilities = _read_base_document(
        root, base, capabilities_file, yaml.safe_load
    )
    if not base_manifest or not base_capabilities:
        return

    committed = _git_files(
        root, "diff", "--name-only", "--no-renames", "-z", base, "HEAD"
    )
    working = _git_files(root, "diff", "--name-only", "--no-renames", "-z", "HEAD")
    working |= _git_files(root, "ls-files", "--others", "--exclude-standard", "-z")
    changed = committed | working
    source_prefix = f"{package_path}/{manifest['sourceRoot'].rstrip('/')}/"
    changed_source = sorted(
        file[len(package_path) + 1 :]
        for file in changed
        if file.startswith(source_prefix) and file.endswith(".py")
    )
    if not changed_source:
        return

    current_usage_files = {
        file for usage in manifest["usages"] for file in usage.get("files", [])
    }
    base_usage_files = {
        file
        for usage in base_manifest.get("usages", [])
        for file in usage.get("files", [])
    }
    current_by_file = {}
    for imported in current_imports:
        current_by_file.setdefault(imported.file, set()).add(imported.symbol)
    base_by_file = {}
    for file in changed_source:
        text = _git_file(root, base, f"{package_path}/{file}")
        if text is not None:
            base_by_file[file] = {
                imported.symbol for imported in _imports_from_text(file, text)
            }
    usage_relevant = [
        file
        for file in changed_source
        if file in current_usage_files
        or file in base_usage_files
        or current_by_file.get(file)
        or base_by_file.get(file)
    ]
    usage_sources = [f"{package_path}/{file}" for file in usage_relevant]
    usage_fresh = _metadata_is_fresh(root, base, working, usage_sources, manifest_file)
    explicit_usage_review = (
        _review_changed(
            base_manifest.get("sourceReview"),
            manifest.get("sourceReview"),
            USAGE_REVIEW_OUTCOME,
        )
        and usage_fresh
    )
    removed_recorded = sorted(
        f"{symbol} in {file}"
        for file in changed_source
        for symbol in base_by_file.get(file, set()) - current_by_file.get(file, set())
        if any(
            usage.get("upstreamSymbol") == symbol and file in usage.get("files", [])
            for usage in manifest["usages"]
        )
    )
    if removed_recorded and not explicit_usage_review:
        errors.append(
            "Removed direct Teams API imports remain recorded: "
            + ", ".join(removed_recorded)
            + f"; update the usage or follow {SOURCE_REVIEW_GUIDE}"
        )
    elif usage_relevant and not (
        (base_manifest.get("usages") != manifest.get("usages") and usage_fresh)
        or explicit_usage_review
    ):
        errors.append(
            f"{len(usage_relevant)} Teams API usage-related source file(s) changed "
            "without a fresh usage-manifest update or non-impact review; see "
            f"{SOURCE_REVIEW_GUIDE}"
        )

    capability_changes = []
    for file in changed_source:
        current_exists = (package_root / file).is_file()
        base_exists = _git_file(root, base, f"{package_path}/{file}") is not None
        current_owners = _owners_for(capabilities, file) if current_exists else []
        base_owners = _owners_for(base_capabilities, file) if base_exists else []
        import_changed = bool(current_owners or base_owners) and (
            sorted(current_by_file.get(file, set()))
            != sorted(base_by_file.get(file, set()))
        )
        if (
            current_exists != base_exists
            or current_owners != base_owners
            or import_changed
        ):
            capability_changes.append(
                {
                    "file": file,
                    "currentExists": current_exists,
                    "baseExists": base_exists,
                    "currentOwners": current_owners,
                    "baseOwners": base_owners,
                    "importChanged": import_changed,
                }
            )
    capability_sources = [
        f"{package_path}/{change['file']}" for change in capability_changes
    ]
    capability_fresh = _metadata_is_fresh(
        root, base, working, capability_sources, capabilities_file
    )
    explicit_capability_review = (
        _review_changed(
            base_capabilities.get("sourceReview"),
            capabilities.get("sourceReview"),
            CAPABILITY_REVIEW_OUTCOME,
        )
        and capability_fresh
    )
    targeted_update = capability_fresh and all(
        _capability_change_addressed(change, base_capabilities, capabilities)
        for change in capability_changes
    )
    if capability_changes and not explicit_capability_review and not targeted_update:
        errors.append(
            f"{len(capability_changes)} capability ownership or upstream-area source "
            "change(s) lack a fresh targeted capability update or non-impact review; "
            f"see {SOURCE_REVIEW_GUIDE}"
        )


def validate_teams_api_metadata(
    manifest_path=MANIFEST,
    capabilities_path=CAPABILITIES,
    package_root=PACKAGE_ROOT,
    repo_root=ROOT,
    base_ref=None,
):
    """Validate current metadata and, when requested, its review against Git."""
    manifest_path = Path(manifest_path).resolve()
    capabilities_path = Path(capabilities_path).resolve()
    package_root = Path(package_root).resolve()
    repo_root = Path(repo_root).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    capabilities = yaml.safe_load(capabilities_path.read_text(encoding="utf-8"))
    errors = []

    if manifest.get("schemaVersion") != 1 or manifest.get("dependency") != DEPENDENCY:
        errors.append(
            "Usage manifest must be a schemaVersion 1 document for the dependency"
        )
    if not isinstance(manifest.get("usages"), list):
        errors.append("Usage manifest must contain a usages array")
    if (
        not isinstance(capabilities, dict)
        or capabilities.get("schemaVersion") != 1
        or capabilities.get("dependency", {}).get("package") != DEPENDENCY
        or not isinstance(capabilities.get("capabilities"), dict)
    ):
        errors.append("Capabilities must be a schemaVersion 1 map for the dependency")
    if errors:
        raise ValueError("; ".join(errors))

    setup_path = package_root / "setup.py"
    if setup_path.is_file():
        requirement = declared_requirement(setup_path.read_text(encoding="utf-8"))
        if manifest.get("declaredVersion") != str(requirement.specifier):
            errors.append(
                "Usage manifest declaredVersion must match setup.py "
                f"({requirement.specifier})"
            )

    for document, outcome, name in (
        (manifest, USAGE_REVIEW_OUTCOME, "usage manifest"),
        (capabilities, CAPABILITY_REVIEW_OUTCOME, "capabilities"),
    ):
        if "sourceReview" in document and not _valid_review(
            document["sourceReview"], outcome
        ):
            errors.append(
                f'{name} sourceReview must use outcome "{outcome}" and include '
                f"a non-empty reason; see {SOURCE_REVIEW_GUIDE}"
            )

    source_root = (package_root / manifest.get("sourceRoot", "")).resolve()
    if not source_root.is_relative_to(package_root) or not source_root.is_dir():
        errors.append("Usage manifest sourceRoot is missing or unsafe")
        source_files = []
    else:
        source_files = _source_files(package_root, source_root)
    source_set = set(source_files)
    represented = set()
    for usage in manifest["usages"]:
        symbol = usage.get("upstreamSymbol") if isinstance(usage, dict) else None
        files = usage.get("files") if isinstance(usage, dict) else None
        if (
            not isinstance(symbol, str)
            or not isinstance(usage.get("usage"), str)
            or not isinstance(files, list)
        ):
            errors.append("Every usage must include upstreamSymbol, usage, and files")
            continue
        for file in files:
            if not isinstance(file, str) or file not in source_set:
                errors.append(
                    f"Usage {symbol} references missing or unsafe file {file!r}"
                )
            else:
                represented.add((symbol, file))
    imports = _collect_imports(package_root, source_files)
    for imported in imports:
        if (imported.symbol, imported.file) not in represented:
            errors.append(
                f"Direct Teams API import {imported.symbol} in {imported.file}:{imported.line} "
                "is absent from the usage manifest"
            )

    for name, capability in capabilities["capabilities"].items():
        owners = capability.get("owners") if isinstance(capability, dict) else None
        areas = (
            capability.get("upstreamAreas") if isinstance(capability, dict) else None
        )
        if not isinstance(owners, list) or not isinstance(areas, list):
            errors.append(f"Capability {name} must include owners and upstreamAreas")
            continue
        for owner in owners:
            if not isinstance(owner, str) or not any(
                _matches_owner(owner, file) for file in source_files
            ):
                errors.append(
                    f"Capability {name} owner {owner!r} matches no source files"
                )
    for imported in imports:
        areas = _upstream_areas(imported.symbol)
        if not areas:
            continue
        owners = _owners_for(capabilities, imported.file)
        if not owners:
            errors.append(
                f"{imported.file} imports {imported.symbol} but has no capability owner"
            )
            continue
        owned_areas = [
            area
            for owner in owners
            for area in capabilities["capabilities"][owner]["upstreamAreas"]
        ]
        if not any(
            candidate == area or candidate.startswith(area + ".")
            for candidate in areas
            for area in owned_areas
        ):
            errors.append(
                f"{imported.symbol} maps to {', '.join(areas)}, absent from "
                f"capability owners {', '.join(owners)} for {imported.file}"
            )

    _validate_static_usage(package_root, source_files, manifest, errors)

    if base_ref:
        _validate_change_reviews(
            repo_root,
            package_root,
            base_ref,
            manifest,
            capabilities,
            imports,
            errors,
            manifest_path,
            capabilities_path,
        )
    if errors:
        raise ValueError(
            "Teams API metadata validation failed:\n- " + "\n- ".join(errors)
        )
    return manifest
