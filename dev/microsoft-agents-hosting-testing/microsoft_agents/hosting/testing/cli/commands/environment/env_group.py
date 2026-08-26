# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Environment CLI commands.

Provides commands to help manage environment settings.
"""

import click


@click.group(name="env")
def env_group():
    """Manage test environments."""
