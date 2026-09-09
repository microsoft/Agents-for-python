# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Install local SDK wheels into an existing exact-candidate environment."""

from email.parser import BytesParser
import os
from pathlib import Path
import shutil
import sys
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from .common import (
    DEPENDENCY,
    PACKAGE,
    PACKAGE_ROOT,
    ROOT,
    declared_requirement,
    python_in,
    run,
    temporary_environment,
    write_json,
)


def prepare_candidate_environment(version, environment, output):
    """Build the SDK and install it beside an already extracted candidate."""
    version = str(Version(version))
    environment = Path(environment).resolve()
    candidate = python_in(environment)
    if not candidate.is_file():
        raise ValueError(
            "Candidate environment does not exist; run compare with --work-root first"
        )
    actual = _installed_version(candidate)
    if Version(actual) != Version(version):
        raise ValueError(f"Candidate environment contains {actual}, expected {version}")

    with temporary_environment(prefix="teams-api-candidate-build-") as work:
        work = Path(work)
        wheel_root = work / "wheels"
        sources = work / "sources"
        build_environment = dict(os.environ, PackageVersion="0.0.0")
        for name in (
            "microsoft-agents-activity",
            "microsoft-agents-hosting-core",
            "microsoft-agents-authentication-msal",
            PACKAGE,
        ):
            source = sources / name
            shutil.copytree(
                ROOT / "libraries" / name,
                source,
                ignore=shutil.ignore_patterns("build", "*.egg-info", "__pycache__"),
            )
            run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    wheel_root,
                    source,
                ],
                env=build_environment,
            )

        run(
            [
                candidate,
                "-m",
                "pip",
                "install",
                "-r",
                ROOT / "scripts/teams-api-drift/requirements.txt",
            ]
        )
        wheels = sorted(wheel_root.glob("*.whl"))
        extension = next(
            wheel
            for wheel in wheels
            if wheel.name.startswith("microsoft_agents_hosting_msteams-")
        )
        dependencies = _extension_dependencies(extension)
        run(
            [
                candidate,
                "-m",
                "pip",
                "install",
                *[wheel for wheel in wheels if wheel != extension],
                *dependencies,
            ]
        )
        # The exact candidate may be outside the published extension's range.
        run([candidate, "-m", "pip", "install", "--no-deps", extension])

    actual = _installed_version(candidate)
    if Version(actual) != Version(version):
        raise ValueError(f"SDK installation replaced candidate {version} with {actual}")
    requirement = declared_requirement(
        (PACKAGE_ROOT / "setup.py").read_text(encoding="utf-8")
    )
    result = {
        "schemaVersion": 1,
        "dependency": DEPENDENCY,
        "version": actual,
        "python": str(candidate),
        "candidateOutsideDeclaredRange": not requirement.specifier.contains(
            actual, prereleases=True
        ),
    }
    write_json(Path(output) / "candidate-environment.json", result)
    return result


def _installed_version(python):
    return run(
        [
            python,
            "-c",
            "from importlib.metadata import version; print(version('microsoft-teams-api'))",
        ]
    ).strip()


def _extension_dependencies(extension):
    with zipfile.ZipFile(extension) as wheel:
        metadata_file = next(
            name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = BytesParser().parsebytes(wheel.read(metadata_file))
    return [
        value
        for value in metadata.get_all("Requires-Dist", [])
        if canonicalize_name(Requirement(value).name) != DEPENDENCY
    ]
