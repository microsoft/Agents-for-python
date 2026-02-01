# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI commands registry.

This module imports and registers all available CLI commands.
Add new commands to the COMMANDS list to make them available.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from click import Command

# Import commands
from .post import post
from .validate import validate
from .chat import chat
from .run import run

# Add commands to this list to register them with the CLI
COMMANDS: list["Command"] = [
    post,
    validate,
    chat,
    run,
]

__all__ = ["COMMANDS"]