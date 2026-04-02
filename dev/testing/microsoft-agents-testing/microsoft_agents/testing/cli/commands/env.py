# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Environment information CLI command.

Displays runtime environment details such as Python version, platform,
working directory, loaded .env variables, and registered scenarios.
"""

import sys
from pathlib import Path

import click

from microsoft_agents.testing.scenario_registry import scenario_registry

from ..core import (
    Output,
    CLIConfig,
    pass_output,
    pass_config,
)

@click.command("env")
@pass_output
@pass_config
def env(config: CLIConfig, out: Output):
    """Show environment information.

    Displays Python version, platform, current directory, loaded
    environment variables, and the number of registered scenarios.

    :param config: The CLI configuration loaded from the .env file.
    :param out: CLI output helper.
    """
    out.info("Environment information:")
    out.info(f"\tPython version: {sys.version}")
    out.info(f"\tPlatform: {sys.platform}")
    out.info(f"\tCurrent working directory: {Path.cwd()}")
    out.info(f"\tRegistered scenarios: {len(scenario_registry)}")
    out.newline()
    out.info(f"\tEnvironment file: {config.env_path if config.env_path else 'None'}")
    out.info("\tEnvironment variables from file:")
    for key, value in config.env.items():
        out.info(f"\t\t{key}={value}")