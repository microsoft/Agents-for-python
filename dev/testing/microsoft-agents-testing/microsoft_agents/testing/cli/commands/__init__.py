# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI commands registry.

This module imports and registers all available CLI commands.
Add new commands to the COMMANDS list to make them available.
"""

from click import Command

# Import commands
from .env import env_group
from .scenario import scenario_group

# Add commands to this list to register them with the CLI
COMMANDS: list[Command] = [
    env_group,
    scenario_group,
]

__all__ = ["COMMANDS"]