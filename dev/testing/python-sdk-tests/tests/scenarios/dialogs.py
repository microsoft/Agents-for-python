# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Dialog scenario for integration testing UserProfileDialog + DialogAgent."""

from microsoft_agents.hosting.core import ConversationState, UserState, Storage
from microsoft_agents.testing import ActivityHandlerScenario, ScenarioConfig

from tests.integration.dialogs.sample.dialog_agent import DialogAgent
from tests.integration.dialogs.sample.user_profile_dialog import UserProfileDialog


def _create_handler(
    conv_state: ConversationState,
    user_state: UserState,
    _storage: Storage,
) -> DialogAgent:
    """Factory consumed by ActivityHandlerScenario."""
    dialog = UserProfileDialog(user_state)
    return DialogAgent(conv_state, user_state, dialog)


def create_dialog_scenario(
    config: ScenarioConfig | None = None,
) -> ActivityHandlerScenario:
    """Create a ready-to-use ActivityHandlerScenario for the UserProfileDialog."""
    return ActivityHandlerScenario(_create_handler, config=config)
