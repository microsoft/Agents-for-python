# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Scenario definition for ActivityHandler-based dialog integration tests."""

from microsoft_agents.hosting.testing import (
    ActivityHandlerEnvironment,
    ActivityHandlerScenario,
    ScenarioConfig,
)

from .sample.dialog_agent import DialogAgent
from .sample.user_profile_dialog import UserProfileDialog


def _create_handler(env: ActivityHandlerEnvironment) -> DialogAgent:
    """Factory consumed by ActivityHandlerScenario."""
    dialog = UserProfileDialog(env.user_state)
    return DialogAgent(env.conversation_state, env.user_state, dialog)


def create_dialog_scenario(
    config: ScenarioConfig | None = None,
) -> ActivityHandlerScenario:
    """Create a ready-to-use ActivityHandlerScenario for the UserProfileDialog."""
    return ActivityHandlerScenario.create(
        _create_handler,
        config=config,
        use_jwt_middleware=False,
    )
