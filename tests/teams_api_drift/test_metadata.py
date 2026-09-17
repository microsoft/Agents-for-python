# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
from pathlib import Path
import subprocess

import pytest
import yaml

from teams_api_drift.metadata import validate_teams_api_metadata


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def metadata_repo(tmp_path):
    package = tmp_path / "libraries/microsoft-agents-hosting-msteams"
    source = package / "microsoft_agents/hosting/msteams"
    source.mkdir(parents=True)
    (source / "activity.py").write_text(
        "from microsoft_teams.api.models.channel_data import ChannelData\n"
        "\n"
        "def event_type(data: ChannelData):\n"
        "    return data.event_type\n",
        encoding="utf-8",
    )
    (package / "setup.py").write_text(
        "from setuptools import setup\n"
        "setup(install_requires=['microsoft-teams-api==2.0.16'])\n",
        encoding="utf-8",
    )
    manifest_path = package / "teams-api-usage-manifest.json"
    manifest = {
        "schemaVersion": 1,
        "dependency": "microsoft-teams-api",
        "declaredVersion": "==2.0.16",
        "sourceRoot": "microsoft_agents/hosting/msteams",
        "usages": [
            {
                "upstreamSymbol": (
                    "microsoft_teams.api.models.channel_data.ChannelData"
                ),
                "usage": "parsed-model",
                "exposure": "publicly-exposed",
                "propertiesRead": ["event_type"],
                "files": ["microsoft_agents/hosting/msteams/activity.py"],
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    capabilities_path = package / "config/teams-capabilities.yaml"
    capabilities_path.parent.mkdir()
    capabilities = {
        "schemaVersion": 1,
        "dependency": {"package": "microsoft-teams-api"},
        "capabilities": {
            "activity-data": {
                "owners": ["microsoft_agents/hosting/msteams"],
                "upstreamAreas": ["microsoft_teams.api.models.channel_data"],
                "adoptionPolicy": "strict-compatibility",
            }
        },
    }
    capabilities_path.write_text(yaml.safe_dump(capabilities), encoding="utf-8")
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "metadata@example.test")
    _git(tmp_path, "config", "user.name", "Metadata Test")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "baseline")
    return {
        "root": tmp_path,
        "package": package,
        "source": source,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "capabilities_path": capabilities_path,
        "capabilities": capabilities,
    }


def _validate(repo, base_ref=None):
    return validate_teams_api_metadata(
        repo["manifest_path"],
        repo["capabilities_path"],
        repo["package"],
        repo["root"],
        base_ref,
    )


def _write_json(path, document):
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def test_accepts_aligned_current_metadata(metadata_repo):
    assert len(_validate(metadata_repo)["usages"]) == 1


def test_rejects_unrecorded_import_and_stale_dependency(metadata_repo):
    metadata_repo["manifest"]["declaredVersion"] = "==2.0.15"
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])
    (metadata_repo["source"] / "extra.py").write_text(
        "from microsoft_teams.api import ApiClient\n", encoding="utf-8"
    )

    with pytest.raises(ValueError) as error:
        _validate(metadata_repo)

    assert "declaredVersion must match setup.py" in str(error.value)
    assert "ApiClient" in str(error.value)


def test_rejects_unrecorded_static_member_and_public_exposure(metadata_repo):
    usage = metadata_repo["manifest"]["usages"][0]
    usage.pop("propertiesRead")
    usage.pop("exposure")
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])

    with pytest.raises(ValueError) as error:
        _validate(metadata_repo)

    assert "event_type is statically read" in str(error.value)
    assert "not marked publicly exposed" in str(error.value)


def test_public_protocol_dunder_annotation_requires_public_exposure(metadata_repo):
    activity = metadata_repo["source"] / "activity.py"
    activity.write_text(
        "from typing import Protocol\n"
        "from microsoft_teams.api.models.channel_data import ChannelData\n"
        "\n"
        "class Handler(Protocol):\n"
        "    def __call__(self, data: ChannelData) -> None: ...\n",
        encoding="utf-8",
    )
    metadata_repo["manifest"]["usages"][0]["exposure"] = "internal-only"
    metadata_repo["manifest"]["usages"][0]["propertiesRead"] = []
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])

    with pytest.raises(ValueError, match="not marked publicly exposed"):
        _validate(metadata_repo)


def test_rejects_unrecorded_static_method_call(metadata_repo):
    activity = metadata_repo["source"] / "activity.py"
    activity.write_text(
        activity.read_text()
        + "\ndef parse(payload):\n"
        + "    return ChannelData.model_validate(payload)\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="model_validate is statically called"):
        _validate(metadata_repo)


def test_source_change_requires_usage_review(metadata_repo):
    activity = metadata_repo["source"] / "activity.py"
    activity.write_text(activity.read_text() + "# implementation refactor\n")

    with pytest.raises(ValueError, match="usage-related source file"):
        _validate(metadata_repo, "main")

    metadata_repo["manifest"]["sourceReview"] = {
        "outcome": "no-usage-metadata-change",
        "reason": "The refactor does not change Teams API consumption.",
    }
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])
    _validate(metadata_repo, "main")


def test_previous_review_does_not_approve_later_source_change(metadata_repo):
    activity = metadata_repo["source"] / "activity.py"
    activity.write_text(activity.read_text() + "# first refactor\n")
    metadata_repo["manifest"]["sourceReview"] = {
        "outcome": "no-usage-metadata-change",
        "reason": "The first refactor preserves Teams API usage.",
    }
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])
    _git(metadata_repo["root"], "add", ".")
    _git(metadata_repo["root"], "commit", "-m", "review first change")
    activity.write_text(activity.read_text() + "# later refactor\n")

    with pytest.raises(ValueError, match="fresh usage-manifest update"):
        _validate(metadata_repo, "main")


def test_new_source_file_requires_capability_review(metadata_repo):
    (metadata_repo["source"] / "new_feature.py").write_text(
        "ENABLED = True\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="capability ownership"):
        _validate(metadata_repo, "main")

    metadata_repo["capabilities"]["sourceReview"] = {
        "outcome": "no-capability-metadata-change",
        "reason": "The helper remains owned by the existing activity capability.",
    }
    metadata_repo["capabilities_path"].write_text(
        yaml.safe_dump(metadata_repo["capabilities"]), encoding="utf-8"
    )
    _validate(metadata_repo, "main")


def test_invalid_review_reason_fails_current_validation(metadata_repo):
    metadata_repo["manifest"]["sourceReview"] = {
        "outcome": "no-usage-metadata-change",
        "reason": "",
    }
    _write_json(metadata_repo["manifest_path"], metadata_repo["manifest"])

    with pytest.raises(ValueError, match="non-empty reason"):
        _validate(metadata_repo)
