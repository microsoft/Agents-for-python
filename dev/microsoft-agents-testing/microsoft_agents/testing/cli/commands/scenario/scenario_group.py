# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Scenario CLI commands.

Provides commands for listing, running, chatting, and posting to
agent test scenarios from the command line.
"""

import click

@click.group(name="scenario")
def scenario_group():
    """Manage test scenarios."""