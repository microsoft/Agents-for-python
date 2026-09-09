# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy
import json

import pytest

from teams_api_drift.classify import classify, read_capabilities, validate_manifest
from teams_api_drift.common import (
    CAPABILITIES,
    DEPENDENCY,
    MANIFEST,
    declared_minimum,
    declared_requirement,
    latest_stable,
    read_json,
)
from teams_api_drift.compare import compare_models, extract_version
from teams_api_drift.resolve import resolve_versions


def symbol(name="microsoft_teams.api.models.Parent", **overrides):
    result = {
        "name": name,
        "kind": "model",
        "properties": {},
        "methods": {},
        "constructors": [],
        "enumMembers": {},
        "exportPaths": [name],
        "deprecated": False,
    }
    result.update(overrides)
    return result


def model(*symbols, version="2.0.0"):
    return {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "version": version,
        "symbols": list(symbols),
    }


def manifest(name="microsoft_teams.api.models.Parent", **overrides):
    usage = {
        "upstreamSymbol": name,
        "usage": "parsed-model",
        "constructsOrValidates": True,
        "exposure": "internal-only",
        "propertiesRead": ["child.value"],
        "files": ["source.py"],
    }
    usage.update(overrides)
    return {"schemaVersion": 1, "dependency": DEPENDENCY, "usages": [usage]}


def capabilities():
    return {
        "capabilities": {
            "models": {
                "upstreamAreas": ["microsoft_teams.api.models"],
                "adoptionPolicy": "review-new-members",
            }
        }
    }


def test_requirement_parsing_does_not_execute_source():
    source = "raise RuntimeError('must not execute')\nsetup(install_requires=['microsoft-teams-api>=2.0.0,<3'])"
    assert declared_minimum(declared_requirement(source)) == "2.0.0"
    assert (
        declared_minimum(
            declared_requirement(
                "setup(install_requires=['microsoft-teams-api==2.0.13.4'])"
            )
        )
        == "2.0.13.4"
    )


@pytest.mark.parametrize(
    "source",
    [
        "setup(install_requires=compute())",
        "setup(install_requires=['microsoft-teams-api<3'])",
        "setup(install_requires=['microsoft-teams-api>2.0.0'])",
        "setup(install_requires=[])",
    ],
)
def test_unsupported_requirement_fails(source):
    with pytest.raises(ValueError):
        declared_minimum(declared_requirement(source))


def test_latest_stable_uses_pep440_and_excludes_yanked_prereleases():
    metadata = {
        "releases": {
            "2.0.13.4": [{}],
            "2.0.14": [{}],
            "3.0.0": [{}],
            "4.0.0": [{"yanked": True}],
            "5.0.0a1": [{}],
            "6.0.0.dev1": [{}],
            "7.0.0": [],
        }
    }
    assert latest_stable(metadata) == "3.0.0"


def test_resolver_detects_requirement_changes_and_normalizes_versions(tmp_path):
    before = "setup(install_requires=['microsoft-teams-api>=2.0.0,<3'])"
    after = "# comment\nsetup(install_requires=['microsoft_teams_api<3,>=2.0.0'])"
    baseline = tmp_path / "baseline.py"
    candidate = tmp_path / "candidate.py"
    baseline.write_text(before)
    candidate.write_text(after)
    # Canonical requirement names are compared independently of spelling.
    result = resolve_versions(baseline, candidate)
    assert not result["changed"]
    assert result["fromVersion"] == "2.0.0"
    assert result["toVersion"] == "2.0.0"

    candidate.write_text(after.replace("2.0.0", "2.0.16"))
    result = resolve_versions(baseline, candidate)
    assert result["changed"]
    assert result["fromVersion"] == "2.0.0"
    assert result["toVersion"] == "2.0.16"


def test_identical_models_ignore_version_and_metadata():
    before, after = model(symbol()), model(symbol(), version="2.0.16")
    before["pythonVersion"] = "3.11.0"
    after["pythonVersion"] = "3.11.1"
    comparison = compare_models(before, after)
    assert not comparison["changed"]
    assert comparison["diff"] == ""


def test_removed_consumed_symbol_blocks_but_unrelated_removal_does_not():
    used, unused = symbol(), symbol("microsoft_teams.api.Unrelated")
    result = classify(
        compare_models(model(used, unused), model(symbol("microsoft_teams.api.Other"))),
        manifest(),
        capabilities(),
    )
    assert result["summary"]["blocking"] == 1
    assert result["summary"]["no-action"] == 2


def test_nested_alias_change_is_required_and_public_exposure_blocks():
    parent = symbol(
        properties={
            "child": {
                "type": "list[microsoft_teams.api.models.Child] | None",
                "optional": True,
            }
        }
    )
    child = symbol(
        "microsoft_teams.api.models.Child",
        properties={
            "value": {"type": "str", "optional": True, "serializationAlias": "oldValue"}
        },
    )
    changed = deepcopy(child)
    changed["properties"]["value"]["serializationAlias"] = "newValue"
    comparison = compare_models(model(parent, child), model(parent, changed))
    result = classify(
        comparison, manifest(propertiesRead=["child[].value"]), capabilities()
    )
    assert result["summary"]["required"] == 1
    assert result["findings"][0]["affectedFiles"] == ["source.py"]
    result = classify(
        comparison,
        manifest(propertiesRead=["child[].value"], exposure="publicly-exposed"),
        capabilities(),
    )
    assert result["summary"]["blocking"] == 1


def test_new_required_field_on_validated_model_blocks_without_explicit_field_read():
    before = symbol()
    after = symbol(properties={"new_field": {"type": "str", "optional": False}})
    result = classify(
        compare_models(model(before), model(after)), manifest(), capabilities()
    )
    assert result["summary"]["blocking"] == 1


def test_unread_field_becoming_required_intersects_model_validation():
    before = symbol(properties={"new_field": {"type": "str", "optional": True}})
    after = symbol(properties={"new_field": {"type": "str", "optional": False}})
    result = classify(
        compare_models(model(before), model(after)), manifest(), capabilities()
    )
    assert result["summary"]["required"] == 1


def test_constructor_change_is_direct_use():
    before = symbol(kind="class", constructors=[{"parameters": []}])
    after = symbol(
        kind="class",
        constructors=[{"parameters": [{"name": "token", "optional": False}]}],
    )
    result = classify(
        compare_models(model(before), model(after)), manifest(), capabilities()
    )
    assert result["summary"]["required"] == 1


def test_optional_constructor_parameter_is_advisory():
    before = symbol(kind="class", constructors=[{"parameters": []}])
    after = symbol(
        kind="class",
        constructors=[{"parameters": [{"name": "timeout", "optional": True}]}],
    )
    result = classify(
        compare_models(model(before), model(after)),
        manifest(exposure="publicly-exposed"),
        capabilities(),
    )
    assert result["summary"]["review"] == 1


def test_additive_feature_and_unrelated_member_policy():
    before, after = symbol(), symbol(
        properties={"new_field": {"type": "str", "optional": True}}
    )
    result = classify(
        compare_models(model(before), model(after)), manifest(), capabilities()
    )
    assert result["findings"][0]["category"] == "feature-review"
    assert result["summary"]["review"] == 1


def test_import_alias_removal_blocks_only_consumers_of_removed_path():
    before = symbol(
        exportPaths=["microsoft_teams.api.Parent", "microsoft_teams.api.models.Parent"]
    )
    after = symbol(exportPaths=["microsoft_teams.api.models.Parent"])
    comparison = compare_models(model(before), model(after))
    assert (
        classify(comparison, manifest("microsoft_teams.api.Parent"), capabilities())[
            "summary"
        ]["blocking"]
        == 1
    )
    assert classify(comparison, manifest(), capabilities())["summary"]["review"] == 1


def test_empty_or_malformed_extraction_fails(tmp_path, monkeypatch):
    monkeypatch.setattr("teams_api_drift.compare.run", lambda *args, **kwargs: "")
    path = tmp_path / "api.json"
    path.write_text(json.dumps(model()))
    with pytest.raises(ValueError):
        extract_version("python", path, "2.0.0")
    with pytest.raises(ValueError):
        compare_models(model(), model(symbol()))


def test_manifest_covers_repository_imports():
    validate_manifest(read_json(MANIFEST))
    read_capabilities(CAPABILITIES)


def test_manifest_detects_unrecorded_import_and_escape(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "use.py").write_text("from microsoft_teams.api import ApiClient\n")
    data = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "sourceRoot": "src",
        "usages": [],
    }
    with pytest.raises(ValueError, match="Unrecorded"):
        validate_manifest(data, tmp_path)
    data["usages"] = [{"upstreamSymbol": "ApiClient", "files": ["../outside.py"]}]
    with pytest.raises(ValueError, match="Invalid usage"):
        validate_manifest(data, tmp_path)
