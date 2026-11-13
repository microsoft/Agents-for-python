# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy
import json

import pytest

from teams_api_drift.classify import classify, validate_manifest
from teams_api_drift import cli
from teams_api_drift.cli import main
from teams_api_drift.common import DEPENDENCY, PACKAGE
from teams_api_drift.report import (
    ADVISORY,
    SECTIONS,
    TITLE,
    prepare_context,
    render_report,
    validate_agent_report,
)


@pytest.fixture
def inputs():
    change = {
        "id": "TSAPI-0001",
        "symbol": "microsoft_teams.api.Client",
        "member": "send",
        "kind": "method-signature-changed",
        "before": [{"parameters": [{"name": "value", "optional": False}]}],
        "after": [{"parameters": [{"name": "value", "optional": True}]}],
        "evidence": ["normalized-api-model"],
    }
    comparison = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "fromVersion": "2.1.0",
        "toVersion": "2.2.0",
        "changes": [change],
    }
    review = {
        "fromVersion": "2.1.0",
        "toVersion": "2.2.0",
        "upstreamSymbol": change["symbol"],
        **{key: deepcopy(change[key]) for key in ("member", "kind", "before", "after")},
        "reason": "Reviewed optional arguments; the adapter supplies the value and its contract is validated.",
    }
    manifest = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "sourceRoot": ".",
        "usages": [
            {
                "upstreamSymbol": change["symbol"],
                "usage": "client-call",
                "methodsCalled": ["send"],
                "exposure": "internal-only",
                "files": ["source.py"],
            }
        ],
        "compatibilityReviews": [review],
    }
    return (
        comparison,
        manifest,
        {"schemaVersion": 1, "dependency": {"package": DEPENDENCY}, "capabilities": {}},
    )


@pytest.mark.parametrize(
    "exposure,original",
    [("internal-only", "required"), ("publicly-exposed", "blocking")],
)
def test_exact_review_preserves_evidence_and_only_changes_classification(
    inputs, exposure, original
):
    comparison, manifest, capabilities = inputs
    manifest["usages"][0]["exposure"] = exposure
    unreviewed = {**manifest, "compatibilityReviews": []}
    assert classify(comparison, unreviewed, capabilities)["summary"][original] == 1
    before = deepcopy(inputs)
    result = classify(*inputs)
    finding = result["findings"][0]
    assert result["summary"] == {
        "blocking": 0,
        "required": 0,
        "review": 0,
        "no-action": 1,
    }
    assert finding["category"] == "reviewed-compatible"
    assert "compatibility-review" in finding["evidence"]
    assert manifest["compatibilityReviews"][0]["reason"] in finding["recommendedAction"]
    assert finding["before"] == comparison["changes"][0]["before"]
    assert finding["after"] == comparison["changes"][0]["after"]
    assert inputs == before
    comparison["changes"][0]["id"] = "TSAPI-9999"
    assert classify(*inputs)["findings"][0]["category"] == "reviewed-compatible"


@pytest.mark.parametrize(
    "field,value",
    [
        ("fromVersion", "2.0.16"),
        ("toVersion", "2.2.1"),
        ("upstreamSymbol", "microsoft_teams.api.Other"),
        ("member", "other"),
        ("member", None),
        ("kind", "method-removed"),
        ("before", None),
        ("after", None),
        ("before", [{"parameters": [{"name": "value", "optional": 0}]}]),
        ("after", [{"parameters": [{"name": "value", "optional": 1}]}]),
    ],
)
def test_stale_or_different_review_does_not_approve_change(inputs, field, value):
    inputs[1]["compatibilityReviews"][0][field] = value
    finding = classify(*inputs)["findings"][0]
    assert finding["classification"] == "required"
    assert "compatibility-review" not in finding["evidence"]


def test_structured_signatures_ignore_object_order_but_preserve_array_order(inputs):
    review = inputs[1]["compatibilityReviews"][0]
    review["before"] = [{"parameters": [{"optional": False, "name": "value"}]}]
    assert classify(*inputs)["findings"][0]["category"] == "reviewed-compatible"
    inputs[0]["changes"][0]["before"].append({"parameters": []})
    review["before"] = list(reversed(inputs[0]["changes"][0]["before"]))
    assert classify(*inputs)["findings"][0]["classification"] == "required"


def test_null_fields_and_historical_reviews(inputs):
    change = inputs[0]["changes"][0]
    change.update(kind="symbol-removed", member=None, after=None)
    review = inputs[1]["compatibilityReviews"][0]
    review.update(kind="symbol-removed", member=None, after=None)
    inputs[1]["compatibilityReviews"].insert(0, {**review, "toVersion": "0.0.1"})
    assert classify(*inputs)["findings"][0]["category"] == "reviewed-compatible"


@pytest.mark.parametrize("reviews", [None, {}, "approved", [None], [{}], [True]])
def test_malformed_review_collection_fails_closed(inputs, reviews):
    inputs[1]["compatibilityReviews"] = reviews
    with pytest.raises(ValueError, match="compatibility review|compatibilityReviews"):
        classify(*inputs)


@pytest.mark.parametrize(
    "field",
    [
        "fromVersion",
        "toVersion",
        "upstreamSymbol",
        "kind",
        "member",
        "before",
        "after",
        "reason",
    ],
)
def test_every_review_field_is_required(inputs, field):
    del inputs[1]["compatibilityReviews"][0][field]
    with pytest.raises(ValueError, match="compatibility review"):
        classify(*inputs)


@pytest.mark.parametrize(
    "field,value",
    [("reason", " "), ("member", ""), ("kind", 1), ("before", float("nan"))],
)
def test_invalid_review_values_fail_manifest_validation(inputs, tmp_path, field, value):
    (tmp_path / "source.py").write_text("")
    inputs[1]["compatibilityReviews"][0][field] = value
    with pytest.raises(ValueError, match="[Cc]ompatibility review"):
        validate_manifest(inputs[1], tmp_path)


def test_reviews_do_not_suppress_feature_or_public_api_findings(inputs):
    inputs[0]["changes"][0]["kind"] = "method-added"
    inputs[1]["compatibilityReviews"][0]["kind"] = "method-added"
    public_api = {
        "schemaVersion": 1,
        "package": PACKAGE,
        "status": "changed",
        "entrypoint": "source.py",
        "publicSymbolChanges": [
            {"kind": "method-added", "symbol": "Client", "releaseDecision": "minor"}
        ],
    }
    result = classify(*inputs, public_api=public_api)
    assert result["summary"]["review"] == 2
    assert all(
        "compatibility-review" not in item["evidence"] for item in result["findings"]
    )


def test_detect_gate_and_reports_with_reviewed_change(inputs, tmp_path, monkeypatch):
    comparison, manifest, capabilities = inputs
    (tmp_path / "source.py").write_text("")
    manifest["sourceRoot"] = str(tmp_path)
    # CLI uses the actual extension root for manifest containment validation.
    monkeypatch.setattr(
        cli, "validate_manifest", lambda data: validate_manifest(data, tmp_path)
    )
    for name, data in (
        ("comparison", comparison),
        ("manifest", manifest),
        ("capabilities", capabilities),
    ):
        (tmp_path / f"{name}.json").write_text(json.dumps(data))
    args = [
        "--comparison",
        str(tmp_path / "comparison.json"),
        "--manifest",
        str(tmp_path / "manifest.json"),
        "--capabilities",
        str(tmp_path / "capabilities.json"),
        "--output",
        str(tmp_path),
        "--fail-on-drift",
    ]
    assert main("detect", args) == 0
    result = json.loads((tmp_path / "findings.json").read_text())
    manifest["compatibilityReviews"][0]["toVersion"] = "2.2.1"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    assert main("detect", args) == 1

    rendered = render_report(result, {"checks": {"build": "failure"}}, tmp_path)
    reviewed_section = rendered.split("## Reviewed compatibility changes")[1].split(
        "## No-action upstream changes"
    )[0]
    assert (
        "TSAPI-0001" in reviewed_section and "compatibility-review" in reviewed_section
    )
    assert "TSAPI-0001" not in rendered.split("## No-action upstream changes")[1]
    assert "build | failure" in rendered
    context = prepare_context(result, manifest, "", rendered, package_root=tmp_path)
    context_findings = context["authoritativeArtifacts"]["findings"]
    assert context_findings["omittedNoActionFindingCount"] == 0
    assert (
        context_findings["findings"][0]["recommendedAction"]
        == result["findings"][0]["recommendedAction"]
    )

    sections = {section: "- No findings in this category." for section in SECTIONS}
    sections["Summary"] = ADVISORY

    def report():
        return (
            TITLE
            + "\n\n"
            + "\n\n".join(f"## {name}\n\n{text}" for name, text in sections.items())
            + "\n"
        )

    assert not validate_agent_report(report(), result)["valid"]
    sections["No action"] = (
        "- **TSAPI-0001** — Advisory: Reviewed optional arguments; compatibility-review evidence records the accepted change."
    )
    assert validate_agent_report(report(), result)["valid"]
    sections["Compatibility breaks"] = sections["No action"]
    sections["No action"] = "- No findings in this category."
    assert not validate_agent_report(report(), result)["valid"]
