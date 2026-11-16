# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Join API changes with explicitly recorded extension use and ownership."""

import ast
import json
from pathlib import Path
import re

import yaml

from .common import DEPENDENCY, PACKAGE, PACKAGE_ROOT, validate_artifact

CLASSIFICATIONS = ("blocking", "required", "review", "no-action")


def read_compatibility_reviews(manifest):
    reviews = manifest.get("compatibilityReviews", [])
    if not isinstance(reviews, list):
        raise ValueError("compatibilityReviews must be an array")
    for review in reviews:
        if (
            not isinstance(review, dict)
            or not all(
                isinstance(review.get(field), str) and review[field].strip()
                for field in (
                    "fromVersion",
                    "toVersion",
                    "upstreamSymbol",
                    "kind",
                    "reason",
                )
            )
            or not all(field in review for field in ("member", "before", "after"))
            or not (
                review["member"] is None
                or isinstance(review["member"], str)
                and review["member"].strip()
            )
        ):
            raise ValueError(
                "Every compatibility review requires versions, upstreamSymbol, kind, "
                "member, before, after, and a non-empty reason; use null for absent fields"
            )
        for field in ("before", "after"):
            try:
                _change_value(review[field])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Compatibility review {field} must be JSON data"
                ) from error
    return reviews


def _change_value(value):
    # JSON comparison ignores object key order but distinguishes false from 0.
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def _matching_review(reviews, comparison, change):
    return next(
        (
            review
            for review in reviews
            if all(
                review[field] == comparison[field]
                for field in ("fromVersion", "toVersion")
            )
            and review["upstreamSymbol"] == change["symbol"]
            and review["kind"] == change["kind"]
            and review["member"] == change.get("member")
            and all(
                _change_value(review[field]) == _change_value(change.get(field))
                for field in ("before", "after")
            )
        ),
        None,
    )


def validate_manifest(manifest, package_root=PACKAGE_ROOT):
    validate_artifact(manifest, "usages")
    read_compatibility_reviews(manifest)
    root = Path(package_root).resolve()
    source = (root / manifest["sourceRoot"]).resolve()
    if not source.is_relative_to(root) or not source.is_dir():
        raise ValueError("Invalid usage source root")
    represented = set()
    for usage in manifest["usages"]:
        if not isinstance(usage.get("upstreamSymbol"), str) or not usage.get("files"):
            raise ValueError("Each usage requires an upstreamSymbol and source files")
        for filename in usage["files"]:
            file = (root / filename).resolve()
            if not file.is_relative_to(source) or not file.is_file():
                raise ValueError(f"Invalid usage source file: {filename}")
            represented.add((usage["upstreamSymbol"], file))
    for file in source.rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("microsoft_teams.api")
            ):
                for name in node.names:
                    if (
                        name.name == "*"
                        or (f"{node.module}.{name.name}", file.resolve())
                        not in represented
                    ):
                        raise ValueError(
                            f"Unrecorded Teams API import: {node.module}.{name.name} in {file.relative_to(root)}"
                        )
            elif isinstance(node, ast.Import):
                for name in node.names:
                    if (
                        name.name.startswith("microsoft_teams.api")
                        and (name.name, file.resolve()) not in represented
                    ):
                        raise ValueError(
                            f"Unrecorded Teams API module import: {name.name}"
                        )
    return manifest


def read_capabilities(path):
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or document.get("schemaVersion") != 1
        or document.get("dependency", {}).get("package") != DEPENDENCY
    ):
        raise ValueError("Expected a schemaVersion 1 Teams API capability map")
    if not isinstance(document.get("capabilities"), dict):
        raise ValueError("Capability map must contain capabilities")
    for item in document["capabilities"].values():
        if item.get("adoptionPolicy") not in (
            "strict-compatibility",
            "review-new-members",
            "advisory-only",
        ) or not isinstance(item.get("upstreamAreas"), list):
            raise ValueError("Invalid capability policy or upstream areas")
    return document


def symbol_index(comparison):
    index = {}
    for symbol in comparison.get("baselineSymbols", []) + comparison.get(
        "candidateSymbols", []
    ):
        index[symbol["name"]] = symbol
        for path in symbol.get("exportPaths", []):
            index[path] = symbol
    return index


def nested_uses(usage, index):
    """Follow recorded field paths through referenced Pydantic models/unions/lists."""
    result = []
    root = index.get(usage["upstreamSymbol"])
    if root is None:
        return result
    for key in ("propertiesRead", "propertiesWritten", "propertiesValidated"):
        for path in usage.get(key, []):
            frontier = [root]
            for member in path.replace("[]", "").split("."):
                next_frontier = []
                for symbol in frontier:
                    result.append((symbol["name"], member))
                    field = symbol.get("properties", {}).get(member, {})
                    for reference in re.findall(
                        r"microsoft_teams\.[\w.]+", field.get("type", "")
                    ):
                        if reference in index:
                            next_frontier.append(index[reference])
                frontier = next_frontier
    return result


def relevant(change, usage, index):
    symbol = index.get(usage["upstreamSymbol"], {})
    same = change["symbol"] in (usage["upstreamSymbol"], symbol.get("name"))
    kind, member = change["kind"], change.get("member")
    if kind.startswith("property-"):
        if (change["symbol"], member) in nested_uses(usage, index):
            return True
        return (
            same
            and (
                kind == "property-added"
                and not change["after"]["optional"]
                or kind == "property-requiredness-changed"
                and change["after"] is False
            )
            and usage.get("constructsOrValidates", False)
        )
    if not same:
        return False
    if kind.startswith("method-"):
        return member in usage.get("methodsCalled", []) or usage.get("exposure") in (
            "publicly-exposed",
            "re-exported",
        )
    if kind == "constructor-changed":
        return usage.get("constructsOrValidates", False)
    return True


def classify(comparison, manifest, capabilities, public_api=None):
    validate_artifact(comparison, "changes")
    validate_artifact(manifest, "usages")
    reviews = read_compatibility_reviews(manifest)
    if public_api is not None and (
        public_api.get("schemaVersion") != 1 or public_api.get("package") != PACKAGE
    ):
        raise ValueError(
            f"Public API report must describe {PACKAGE} using schemaVersion 1"
        )
    index = symbol_index(comparison)
    exposed = {
        item["upstreamSymbol"]
        for item in (public_api or {}).get("upstreamTypeLeaks", [])
    }
    findings = []
    for change in comparison["changes"]:
        uses = [usage for usage in manifest["usages"] if relevant(change, usage, index)]
        candidates = [
            (len(area), name, config)
            for name, config in capabilities["capabilities"].items()
            for area in config["upstreamAreas"]
            if change["symbol"] == area or change["symbol"].startswith(area + ".")
        ]
        owner = sorted(candidates, key=lambda entry: (-entry[0], entry[1]))
        capability, policy = (
            (owner[0][1], owner[0][2]["adoptionPolicy"]) if owner else (None, None)
        )
        classification, category = "no-action", None
        publicly_exposed = change["symbol"] in exposed or any(
            u.get("exposure") in ("publicly-exposed", "re-exported")
            or u["upstreamSymbol"] in exposed
            for u in uses
        )
        if uses:
            kind = change["kind"]
            if kind.endswith("-removed") or kind == "symbol-kind-changed":
                classification = "blocking"
            elif kind == "property-added" and not change["after"]["optional"]:
                classification = "blocking"
            elif kind in ("deprecation-changed", "enum-member-added", "method-added"):
                classification = "review"
            elif (
                kind in ("constructor-changed", "method-signature-changed")
                and change.get("compatibility") == "non-breaking"
            ):
                classification = "review"
            elif kind == "export-path-changed":
                removed = set(change["before"]) - set(change["after"])
                classification = (
                    "blocking"
                    if any(u["upstreamSymbol"] in removed for u in uses)
                    else "review"
                )
            else:
                classification = "blocking" if publicly_exposed else "required"
        elif change["kind"].endswith("-added") and policy in (
            "strict-compatibility",
            "review-new-members",
        ):
            classification = "review"
            category = (
                "internal-opportunity"
                if policy == "strict-compatibility"
                else "feature-review"
            )
        action = {
            "blocking": "Adapt this consumed contract before adopting the candidate version.",
            "required": "Review and adapt the affected mapping, validation or call contract.",
            "review": "Review this upstream change; adoption requires a maintainer decision.",
            "no-action": "No recorded extension usage intersects this change.",
        }[classification]
        review = (
            _matching_review(reviews, comparison, change)
            if classification in ("blocking", "required")
            else None
        )
        if review is not None:
            classification, category = "no-action", "reviewed-compatible"
            action = f"Reviewed compatibility change: {review['reason']}"
        findings.append(
            {
                "id": change["id"],
                "source": "api-diff",
                "classification": classification,
                "category": category,
                "kind": change["kind"],
                "upstreamSymbol": change["symbol"],
                "member": change.get("member"),
                "capability": capability,
                "usageKinds": sorted({u["usage"] for u in uses}),
                "exposure": (
                    "publicly-exposed"
                    if publicly_exposed
                    else "runtime-used" if uses else "unknown"
                ),
                "affectedFiles": sorted({f for u in uses for f in u["files"]}),
                "before": change.get("before"),
                "after": change.get("after"),
                "evidence": sorted(
                    set(
                        change["evidence"]
                        + ["dependency-usage"]
                        + (["teams-capabilities"] if capability else [])
                        + (["compatibility-review"] if review is not None else [])
                    )
                ),
                "recommendedAction": action,
            }
        )
    if public_api and public_api.get("status") == "changed":
        for number, change in enumerate(public_api["publicSymbolChanges"], 1):
            findings.append(
                {
                    "id": f"EXTAPI-{number:04d}",
                    "source": "public-api",
                    "classification": "review",
                    "kind": change["kind"],
                    "upstreamSymbol": change["symbol"],
                    "affectedFiles": [public_api["entrypoint"]],
                    "usageKinds": ["public-api"],
                    "exposure": "publicly-exposed",
                    "evidence": ["public-api-report"],
                    "recommendedAction": f"Review {change['releaseDecision']} release impact.",
                }
            )
    result = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "fromVersion": comparison["fromVersion"],
        "toVersion": comparison["toVersion"],
        "summary": {
            key: sum(f["classification"] == key for f in findings)
            for key in CLASSIFICATIONS
        },
        "findings": findings,
    }
    if public_api:
        result["publicApi"] = public_api
    return result
