# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Deterministic evidence rendering and bounded advisory report contracts."""

import json
from pathlib import Path
import re

from .common import DEPENDENCY, PACKAGE, PACKAGE_ROOT, validate_artifact

SECTIONS = [
    "Summary",
    "Compatibility breaks",
    "Required adaptations",
    "Feature-review candidates",
    "Internal implementation opportunities",
    "Maintainer decisions",
    "No action",
    "Suggested implementation issues",
    "Validation checklist",
]
ADVISORY = "This is an advisory report; it does not make or authorize implementation decisions."
TITLE = "# teams.api Impact Report"
ID_PATTERN = r"\b(?:TSAPI|EXTAPI)-[A-Za-z0-9-]+\b"
MAX_CONTEXT_CHARACTERS = 60_000
MAX_SOURCE_CHARACTERS = 12_000
MAX_ADVISORY_REVIEW_FINDINGS = 24
MAX_REPORT_CHARACTERS = 4_000


def advisory_finding(finding):
    """Keep the evidence needed to write an advisory, without raw API models."""
    return {
        key: finding[key]
        for key in (
            "id",
            "classification",
            "category",
            "kind",
            "upstreamSymbol",
            "member",
            "capability",
            "usageKinds",
            "exposure",
            "affectedFiles",
            "evidence",
            "recommendedAction",
        )
        if key in finding and finding[key] is not None
    }


def validate_findings(findings):
    validate_artifact(findings, "findings")
    ids = []
    for finding in findings["findings"]:
        if not isinstance(finding, dict) or finding.get("classification") not in (
            "blocking",
            "required",
            "review",
            "no-action",
        ):
            raise ValueError("Invalid finding classification")
        if not re.fullmatch(ID_PATTERN, finding.get("id", "")):
            raise ValueError("Invalid finding ID")
        ids.append(finding["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate finding IDs")
    return findings


def render_report(findings, summary, artifact_directory):
    if findings is not None:
        validate_findings(findings)
    checks = summary.get("checks", {})
    lines = [
        "# teams.api Deterministic Impact Report",
        "",
        "Generated from deterministic evidence; this report contains no AI conclusions.",
        "",
        "## Compared versions",
        "",
    ]
    if findings is None:
        lines += ["Analysis is incomplete. No compatibility conclusion is available."]
    else:
        lines += [
            f"Compared `{DEPENDENCY}` **{findings['fromVersion']}** to **{findings['toVersion']}** for `{PACKAGE}`."
        ]
    if summary.get("candidateDiffersFromPinnedVersion"):
        lines += [
            "",
            "The candidate differs from the extension's pinned dependency version. Tests explicitly install it in a disposable environment; package metadata is unchanged.",
        ]
    lines += ["", "## Build and test status", "", "| Check | Status |", "| --- | --- |"]
    lines += [f"| {name} | {status} |" for name, status in sorted(checks.items())]
    if findings is not None:
        for title, predicate in (
            (
                "Blocking compatibility issues",
                lambda f: f["classification"] == "blocking",
            ),
            ("Required adaptations", lambda f: f["classification"] == "required"),
            (
                "Feature-review candidates",
                lambda f: f.get("category") == "feature-review",
            ),
            (
                "Internal implementation opportunities",
                lambda f: f.get("category") == "internal-opportunity",
            ),
            (
                "Maintainer decisions required",
                lambda f: f["classification"] == "review" and not f.get("category"),
            ),
            (
                "No-action upstream changes",
                lambda f: f["classification"] == "no-action",
            ),
        ):
            lines += ["", f"## {title}", ""]
            selected = sorted(
                filter(predicate, findings["findings"]),
                key=lambda f: (f.get("capability") or "", f["id"]),
            )
            for item in selected:
                symbol = item["upstreamSymbol"] + (
                    "." + item["member"] if item.get("member") else ""
                )
                lines += [
                    f"- **{item['id']}** — `{symbol}` ({item['kind']}; {item['classification']}). {item['recommendedAction']}",
                    f"  Files: {', '.join(item['affectedFiles']) or 'No directly affected source file'}.",
                    f"  Evidence: {', '.join(item['evidence'])}.",
                ]
            if not selected:
                lines += ["No findings in this category."]
        lines += [
            "",
            "## Public API impact",
            "",
            (
                json.dumps(findings["publicApi"], sort_keys=True)
                if findings.get("publicApi")
                else "A separate extension public API comparison was not supplied. Recorded public type exposure is included in compatibility classification."
            ),
        ]
    lines += ["", "## Artifacts", ""]
    lines += [
        f"- [{file.name}]({file.name})"
        for file in sorted(Path(artifact_directory).glob("*"))
        if file.is_file() and file.name != "deterministic-report.md"
    ]
    return "\n".join(lines) + "\n"


def redact_source(text):
    text = re.sub(
        r"(?i)(authorization\s*[:=]\s*['\"]?)(?:bearer\s+)?[^'\"\s,}]+",
        r"\1[REDACTED]",
        text,
    )
    return re.sub(
        r"(?i)((?:client_?secret|api_?key|password|token)\s*[:=]\s*['\"])[^'\"]+",
        r"\1[REDACTED]",
        text,
    )


def prepare_context(
    findings,
    manifest,
    capabilities_text,
    deterministic_report,
    summary=None,
    public_api=None,
    package_root=PACKAGE_ROOT,
):
    validate_findings(findings)
    validate_artifact(manifest, "usages")
    root = Path(package_root).resolve()
    source = (root / manifest["sourceRoot"]).resolve()
    if not source.is_relative_to(root):
        raise ValueError("Source root must be inside the extension")
    selected, omitted = [], []
    actionable = [
        item for item in findings["findings"] if item["classification"] != "no-action"
    ]
    mandatory = [
        item
        for item in actionable
        if item["classification"] in ("blocking", "required")
    ]
    reviews = [item for item in actionable if item["classification"] == "review"]
    included_findings = mandatory + reviews[:MAX_ADVISORY_REVIEW_FINDINGS]
    omitted_reviews = reviews[MAX_ADVISORY_REVIEW_FINDINGS:]
    paths = sorted({f for item in included_findings for f in item["affectedFiles"]})
    source_characters = 0
    for filename in paths:
        # Normalize separators before containment checks on all platforms.
        path = (root / filename.replace("\\", "/")).resolve()
        if (
            not path.is_relative_to(source)
            or not path.is_file()
            or path.suffix != ".py"
        ):
            omitted.append(filename)
            continue
        content = redact_source(path.read_text(encoding="utf-8"))
        original_length = len(content)
        remaining = MAX_SOURCE_CHARACTERS - source_characters
        if remaining <= 0:
            omitted.append(filename)
            continue
        content = content[: min(MAX_SOURCE_CHARACTERS, remaining)]
        selected.append(
            {
                "path": path.relative_to(root).as_posix(),
                "content": content,
                "truncated": len(content) < original_length,
            }
        )
        source_characters += len(content)
    authoritative = {
        "findings": {
            "schemaVersion": findings["schemaVersion"],
            "dependency": findings["dependency"],
            "fromVersion": findings["fromVersion"],
            "toVersion": findings["toVersion"],
            "summary": findings["summary"],
            "findings": [advisory_finding(item) for item in included_findings],
            "omittedReviewFindingIds": [item["id"] for item in omitted_reviews],
            "omittedNoActionFindingCount": sum(
                item["classification"] == "no-action" for item in findings["findings"]
            ),
        },
        "usageManifest": manifest,
        "capabilitiesYaml": capabilities_text,
        "deterministicReport": deterministic_report[:MAX_REPORT_CHARACTERS],
    }
    if summary is not None:
        authoritative["testSummary"] = summary
    if public_api is not None:
        authoritative["publicApiReport"] = public_api
    result = {
        "schemaVersion": 1,
        "package": PACKAGE,
        "dependency": DEPENDENCY,
        "authoritativeArtifacts": authoritative,
        "relevantSourceFiles": selected,
        "omittedSourceFiles": omitted,
    }
    if len(json.dumps(result, ensure_ascii=False)) > MAX_CONTEXT_CHARACTERS:
        raise ValueError("Bounded advisory context exceeds its total size limit")
    return result


def validate_agent_report(report, findings):
    validate_findings(findings)
    report = report.replace("\r\n", "\n")
    errors = []
    if not report.startswith(TITLE + "\n"):
        errors.append(f'Report must start with "{TITLE}".')
    headings = re.findall(r"^## (.+)$", report, re.M)
    if headings != SECTIONS:
        errors.append(
            "Required sections must appear exactly once and in the required order, on separate lines."
        )
    sections = {}
    for match in re.finditer(r"^## ([^\n]+)\n([\s\S]*?)(?=^## |\Z)", report, re.M):
        sections[match[1]] = match[2]
        if not match[2].startswith("\n"):
            errors.append(f"A blank line is required after {match[1]}.")
    if not sections.get("Summary", "").lstrip().startswith(ADVISORY):
        errors.append(f"Summary section must start with: {ADVISORY}")
    known = {item["id"] for item in findings["findings"]}
    referenced = set(re.findall(ID_PATTERN, report))
    unknown = sorted(referenced - known)
    missing = sorted(
        item["id"]
        for item in findings["findings"]
        if item["classification"] in ("blocking", "required")
        and item["id"] not in referenced
    )
    if unknown:
        errors.append("Unknown finding IDs: " + ", ".join(unknown))
    if missing:
        errors.append("Missing blocking or required finding IDs: " + ", ".join(missing))
    for section in SECTIONS[1:-1]:
        for line in sections.get(section, "").splitlines():
            aggregate_no_action = section == "No action" and re.search(
                r"\bno action\b", line, re.I
            )
            if (
                re.match(r"\s*(?:[-*+]|\d+[.)])\s", line)
                and not re.search(ID_PATTERN, line)
                and not re.match(r"\s*- No ", line, re.I)
                and not aggregate_no_action
            ):
                errors.append("Action item is not tied to a finding ID: " + line)
    return {
        "schemaVersion": 1,
        "valid": not errors,
        "referencedFindingIds": sorted(referenced),
        "missingMandatoryFindingIds": missing,
        "unknownFindingIds": unknown,
        "errors": errors,
    }
