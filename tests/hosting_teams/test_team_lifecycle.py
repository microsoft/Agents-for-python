# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.teams (team lifecycle conversation update events)."""

import pytest

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_agents.hosting.teams import TeamsAgentExtension


class TestTeamLifecycle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def _selector_for(self, event_type: str):
        """Register a no-op handler and return the registered selector."""
        self.app._routes.clear()

        async def handler(ctx, state, data): ...

        return handler

    def test_archived_selector(self):
        @self.ext.teams.archived()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamArchived"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamDeleted"},
                )
            )
            is False
        )

    def test_deleted_selector(self):
        @self.ext.teams.deleted()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamDeleted"},
                )
            )
            is True
        )

    def test_hard_deleted_selector(self):
        @self.ext.teams.hard_deleted()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamHardDeleted"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamDeleted"},
                )
            )
            is False
        )

    def test_renamed_selector(self):
        @self.ext.teams.renamed()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamRenamed"},
                )
            )
            is True
        )

    def test_restored_selector(self):
        @self.ext.teams.restored()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamRestored"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamArchived"},
                )
            )
            is False
        )

    def test_unarchived_selector(self):
        @self.ext.teams.unarchived()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamUnarchived"},
                )
            )
            is True
        )

    def test_team_event_requires_msteams_channel(self):
        @self.ext.teams.archived()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_id="webchat",
                    channel_data={"eventType": "teamArchived"},
                )
            )
            is False
        )

    def test_team_event_is_not_invoke(self):
        @self.ext.teams.archived()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is False
