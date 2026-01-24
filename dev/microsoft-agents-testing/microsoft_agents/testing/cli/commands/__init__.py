# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI commands registry."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from click import Command

# Import commands
from .health import health
from .post import post
from .validate import validate
from .console import console
from .run import run

# Add commands to this list to register them with the CLI
COMMANDS: list["Command"] = [
    health,
    post,
    validate,
    console,
    run,
]

__all__ = ["COMMANDS"]