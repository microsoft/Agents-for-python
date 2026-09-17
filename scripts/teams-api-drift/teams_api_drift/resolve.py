# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Resolve declared Teams API versions from explicit setup.py inputs."""

from pathlib import Path

from .common import DEPENDENCY, declared_requirement, declared_version, latest_stable


def resolve_versions(setup_path, compare_path=None, include_latest=False):
    """Return normalized requirements and exact comparison versions."""
    baseline = declared_requirement(Path(setup_path).read_text(encoding="utf-8"))
    result = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "requirement": str(baseline.specifier),
        "fromVersion": declared_version(baseline),
    }
    if compare_path is not None:
        candidate = declared_requirement(Path(compare_path).read_text(encoding="utf-8"))
        result.update(
            {
                "candidateRequirement": str(candidate.specifier),
                "toVersion": declared_version(candidate),
                "changed": declared_version(baseline) != declared_version(candidate),
            }
        )
    elif include_latest:
        result["toVersion"] = latest_stable()
        result["changed"] = result["fromVersion"] != result["toVersion"]
    return result
