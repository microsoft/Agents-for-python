# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Unified command-line interface for Teams API drift tooling."""

import argparse
import json
from pathlib import Path
import sys

from importlib.metadata import version

from .candidate import prepare_candidate_environment
from .classify import classify, read_capabilities, validate_manifest
from .common import (
    ARTIFACTS,
    CAPABILITIES,
    DEPENDENCY,
    MANIFEST,
    destination,
    read_json,
    write_json,
    write_text,
)
from .compare import compare_versions
from .report import prepare_context, render_report, validate_agent_report
from .resolve import resolve_versions

TOOL_COMMANDS = (
    "resolve",
    "verify-usage",
    "compare",
    "prepare-candidate",
    "detect",
    "summary",
    "render",
    "prepare",
    "validate",
)


def entrypoint(argv=None):
    """Dispatch one public subcommand to its focused parser and implementation."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in ("-h", "--help"):
        print("usage: teams-api-drift.py COMMAND [OPTIONS]")
        print()
        print("commands:")
        for command in TOOL_COMMANDS:
            print(f"  {command}")
        return 0 if arguments else 2
    command = arguments.pop(0)
    if command not in TOOL_COMMANDS:
        print(f"teams-api-drift.py: unknown command: {command}", file=sys.stderr)
        return 2
    return main(command, arguments)


def main(command=None, argv=None):
    parser = argparse.ArgumentParser(
        prog=f"teams-api-drift.py {command}" if command else "teams-api-drift.py",
        description="Teams API drift analysis",
    )
    parser.add_argument("--output", "-o", type=Path, default=ARTIFACTS)
    if command == "compare":
        parser.add_argument("candidate", nargs="?")
        parser.add_argument("--from", dest="baseline")
        parser.add_argument("--to")
        parser.add_argument("--work-root", type=Path)
        parser.add_argument("--verbose", "-v", action="store_true")
    elif command == "resolve":
        parser.add_argument("--setup", type=Path, required=True)
        parser.add_argument("--compare", type=Path)
        parser.add_argument("--latest-stable", action="store_true")
    elif command == "verify-usage":
        parser.add_argument("--manifest", "-m", type=Path, default=MANIFEST)
        parser.add_argument("--capabilities", type=Path, default=CAPABILITIES)
    elif command == "prepare-candidate":
        parser.add_argument("--version", required=True)
        parser.add_argument("--environment", type=Path, required=True)
    elif command == "detect":
        parser.add_argument(
            "--comparison", "-c", type=Path, default=ARTIFACTS / "raw-api-diff.json"
        )
        parser.add_argument("--manifest", "-m", type=Path, default=MANIFEST)
        parser.add_argument("--capabilities", type=Path, default=CAPABILITIES)
        parser.add_argument("--public-api-report", type=Path)
        parser.add_argument("--fail-on-drift", action="store_true")
    elif command == "summary":
        for option in (
            "build",
            "usage-collection",
            "api-extraction",
            "api-comparison",
            "contract-tests",
            "boundary-tests",
        ):
            parser.add_argument(
                "--" + option,
                choices=("success", "failure", "skipped", "cancelled"),
                default="skipped",
            )
        parser.add_argument("--candidate-environment", type=Path)
    elif command in ("render", "prepare", "validate"):
        parser.add_argument(
            "--findings", "-f", type=Path, default=ARTIFACTS / "findings.json"
        )
        if command in ("render", "prepare"):
            parser.add_argument("--test-summary", type=Path)
        if command == "render":
            parser.add_argument("--allow-incomplete", action="store_true")
        if command == "prepare":
            parser.add_argument("--usage-manifest", type=Path, default=MANIFEST)
            parser.add_argument("--capabilities", type=Path, default=CAPABILITIES)
            parser.add_argument(
                "--deterministic-report",
                type=Path,
                default=ARTIFACTS / "deterministic-report.md",
            )
            parser.add_argument("--public-api-report", type=Path)
        if command == "validate":
            parser.add_argument(
                "--report", type=Path, default=ARTIFACTS / "agent-report.md"
            )
    args = parser.parse_args(argv)
    try:
        if command == "compare":
            if args.to and args.candidate:
                parser.error("Use either --to or a positional candidate, not both")
            result = compare_versions(
                args.baseline or version(DEPENDENCY),
                args.to or args.candidate,
                args.output,
                args.work_root,
            )
            print(
                f"Compared {result['fromVersion']} to {result['toVersion']}: {len(result['changes'])} changes"
            )
            if args.verbose:
                print(result["diff"])
        elif command == "resolve":
            result = resolve_versions(
                args.setup, args.compare, include_latest=args.latest_stable
            )
            write_json(destination(args.output, "resolved-versions.json"), result)
            print(json.dumps(result))
        elif command == "verify-usage":
            manifest = validate_manifest(read_json(args.manifest))
            read_capabilities(args.capabilities)
            print(f"Verified {len(manifest['usages'])} Teams API usages")
        elif command == "prepare-candidate":
            result = prepare_candidate_environment(
                args.version, args.environment, args.output
            )
            print(json.dumps(result))
        elif command == "detect":
            result = classify(
                read_json(args.comparison),
                validate_manifest(read_json(args.manifest)),
                read_capabilities(args.capabilities),
                read_json(args.public_api_report) if args.public_api_report else None,
            )
            write_json(destination(args.output, "findings.json"), result)
            return int(
                args.fail_on_drift
                and (
                    result["summary"]["blocking"] > 0
                    or result["summary"]["required"] > 0
                )
            )
        elif command == "summary":
            names = {
                "build": "build",
                "usage_collection": "usageCollection",
                "api_extraction": "apiExtraction",
                "api_comparison": "apiComparison",
                "contract_tests": "contractTests",
                "boundary_tests": "boundaryTests",
            }
            summary = {
                "schemaVersion": 1,
                "checks": {value: getattr(args, key) for key, value in names.items()},
            }
            if args.candidate_environment:
                candidate = read_json(args.candidate_environment)
                summary.update(
                    {
                        "toVersion": candidate["version"],
                        "candidateOutsideDeclaredRange": candidate[
                            "candidateOutsideDeclaredRange"
                        ],
                    }
                )
            write_json(destination(args.output, "test-summary.json"), summary)
        elif command == "render":
            target = destination(args.output, "deterministic-report.md")
            if args.findings.is_file():
                findings = read_json(args.findings)
            elif args.allow_incomplete:
                findings = None
            else:
                raise FileNotFoundError(args.findings)
            write_text(
                target,
                render_report(
                    findings,
                    read_json(args.test_summary) if args.test_summary else {},
                    target.parent,
                ),
            )
        elif command == "prepare":
            result = prepare_context(
                read_json(args.findings),
                read_json(args.usage_manifest),
                args.capabilities.read_text(encoding="utf-8"),
                args.deterministic_report.read_text(encoding="utf-8"),
                read_json(args.test_summary) if args.test_summary else None,
                read_json(args.public_api_report) if args.public_api_report else None,
            )
            write_json(destination(args.output, "agent-context.json"), result)
        elif command == "validate":
            result = validate_agent_report(
                args.report.read_text(encoding="utf-8"), read_json(args.findings)
            )
            write_json(destination(args.output, "agent-report-validation.json"), result)
            print(json.dumps(result))
            return int(not result["valid"])
    except Exception as error:
        print(f"Teams API drift error: {error}", file=sys.stderr)
        return 1
    return 0
