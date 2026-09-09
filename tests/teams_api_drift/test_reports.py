# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

import pytest

from teams_api_drift.common import DEPENDENCY
from teams_api_drift.report import (
    ADVISORY,
    MAX_CONTEXT_CHARACTERS,
    SECTIONS,
    TITLE,
    prepare_context,
    render_report,
    validate_agent_report,
)


def findings():
    return {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "fromVersion": "2.0.16",
        "toVersion": "2.0.17",
        "summary": {"blocking": 1, "required": 0, "review": 0, "no-action": 0},
        "findings": [
            {
                "id": "TSAPI-0001",
                "classification": "blocking",
                "upstreamSymbol": "ApiClient",
                "kind": "constructor-changed",
                "affectedFiles": ["src/client.py"],
                "evidence": ["normalized-api-model"],
                "recommendedAction": "Review constructor.",
            }
        ],
    }


def report(**overrides):
    content = {section: "- No supported items." for section in SECTIONS}
    content.update(
        {
            "Summary": ADVISORY,
            "Compatibility breaks": "- TSAPI-0001 Advisory: Update constructor.",
        }
    )
    content.update(overrides)
    return (
        TITLE
        + "\n\n"
        + "\n\n".join(f"## {section}\n\n{content[section]}" for section in SECTIONS)
        + "\n"
    )


def test_valid_advisory_and_extended_summary():
    assert validate_agent_report(
        report(Summary=ADVISORY + " Additional context."), findings()
    )["valid"]
    assert validate_agent_report(report().replace("\n", "\r\n"), findings())["valid"]


@pytest.mark.parametrize(
    "alter",
    [
        lambda text: text.replace("TSAPI-0001", "TSAPI-9999"),
        lambda text: text.replace("## No action", "## Summary"),
        lambda text: text.replace("## Summary", "## Summary narrative"),
        lambda text: text.replace(ADVISORY, "An advisory report"),
        lambda text: text.replace(
            "## Compatibility breaks\n\n", "## Compatibility breaks\n"
        ),
        lambda text: text.replace(
            "## No action\n\n- No supported items.",
            "## No action\n\n- Unsupported action.",
        ),
        lambda text: text.replace("## No action", "## Required adaptations", 1),
    ],
)
def test_malformed_reports_are_rejected(alter):
    assert not validate_agent_report(alter(report()), findings())["valid"]


def test_missing_findings_and_unattributed_numbered_actions():
    result = validate_agent_report(
        report(**{"Compatibility breaks": "1. Update constructor."}), findings()
    )
    assert result["missingMandatoryFindingIds"] == ["TSAPI-0001"]
    assert any("not tied" in error for error in result["errors"])


def test_cross_cutting_test_failure_belongs_in_validation_checklist():
    advisory = (
        "- **Advisory:** Investigate why boundary tests and contract tests failed "
        "despite successful API extraction."
    )
    invalid = validate_agent_report(
        report(**{"Maintainer decisions": advisory}), findings()
    )
    assert any(advisory in error for error in invalid["errors"])

    valid = validate_agent_report(
        report(**{"Validation checklist": advisory}), findings()
    )
    assert valid["valid"]


def test_no_action_section_allows_an_aggregate_omitted_finding_count():
    result = validate_agent_report(
        report(
            **{
                "No action": "- 147 additional changes in the dependency require no action."
            }
        ),
        findings(),
    )
    assert result["valid"]


def test_render_is_deterministic_and_links_only_existing_artifacts(tmp_path):
    (tmp_path / "findings.json").write_text("{}")
    first = render_report(findings(), {"checks": {"build": "failure"}}, tmp_path)
    assert first == render_report(
        findings(), {"checks": {"build": "failure"}}, tmp_path
    )
    assert "build | failure" in first
    assert "[findings.json](findings.json)" in first
    assert "agent-report.md" not in first
    assert "incomplete" in render_report(None, {}, tmp_path)


def test_context_redacts_bounds_and_confines_sources(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "client.py").write_text('token = "secret"\n' + "x" * 13000)
    data = findings()
    data["findings"][0]["affectedFiles"] += [
        "../outside.py",
        "src/../../outside.py",
        "src/missing.py",
    ]
    manifest = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "sourceRoot": "src",
        "usages": [],
    }
    context = prepare_context(data, manifest, "", "", package_root=tmp_path)
    assert len(context["relevantSourceFiles"]) == 1
    selected = context["relevantSourceFiles"][0]
    assert "secret" not in selected["content"]
    assert "[REDACTED]" in selected["content"]
    assert selected["truncated"] and len(selected["content"]) == 12000
    assert len(context["omittedSourceFiles"]) == 3


def test_context_bounds_total_input_and_preserves_mandatory_findings(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "client.py").write_text("x" * 14000)
    data = findings()
    data["findings"] += [
        {
            **data["findings"][0],
            "id": f"TSAPI-{number:04d}",
            "classification": "review",
        }
        for number in range(2, 50)
    ]
    data["summary"] = {"blocking": 1, "required": 0, "review": 48, "no-action": 0}
    manifest = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "sourceRoot": "src",
        "usages": [],
    }

    context = prepare_context(
        data, manifest, "capabilities: {}", "report", package_root=tmp_path
    )

    advisory = context["authoritativeArtifacts"]["findings"]
    assert advisory["findings"][0]["id"] == "TSAPI-0001"
    assert len(advisory["findings"]) == 25
    assert len(advisory["omittedReviewFindingIds"]) == 24
    assert sum(len(item["content"]) for item in context["relevantSourceFiles"]) <= 12000
    assert len(json.dumps(context, ensure_ascii=False)) <= MAX_CONTEXT_CHARACTERS


def test_wrong_dependency_and_duplicate_ids_fail():
    data = findings()
    data["dependency"] = "other"
    with pytest.raises(ValueError):
        validate_agent_report(report(), data)
    data = findings()
    data["findings"] *= 2
    with pytest.raises(ValueError, match="Duplicate"):
        validate_agent_report(report(), data)
