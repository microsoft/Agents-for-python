# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import click

from microsoft_agents.testing.cli.core import (
    pass_output,
    Output
)
from microsoft_agents.testing.scenario_registry import scenario_registry

from .scenario_group import scenario_group

@scenario_group.command("list")
@click.argument("pattern", default="*")
@pass_output
def _list(out: Output, pattern: str) -> None:
    """List registered test scenarios matching a pattern.

    :param out: CLI output helper.
    :param pattern: Glob-style pattern to filter scenario names.
    """
    matched_scenarios = scenario_registry.discover(pattern)

    out.newline()
    out.info(f"Matching scenarios to pattern '{pattern}':")
    if not matched_scenarios:
        out.info("No scenarios found matching the pattern.")
        return
    out.newline()

    for name, entry in matched_scenarios.items():
        out.info(f"\t{name}: {entry.description}")
    out.newline()
