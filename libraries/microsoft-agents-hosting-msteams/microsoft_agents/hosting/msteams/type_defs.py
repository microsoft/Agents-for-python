# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Shared type aliases and protocols used across the Teams hosting sub-package."""

from typing import TYPE_CHECKING

from typing import (
    Callable,
    Pattern,
)

if TYPE_CHECKING:
    from .teams_turn_context import TeamsTurnContext

TeamsRouteSelector = Callable[["TeamsTurnContext"], bool]
CommandSelector = str | Pattern[str] | None
