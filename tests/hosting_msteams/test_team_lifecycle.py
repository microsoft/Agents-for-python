# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.teams (team lifecycle conversation update events)."""

import pytest

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_agents.hosting.msteams import TeamsAgentExtension


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


class TestTeamEvent:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def _selector(self):
        @self.ext.teams.event()
        async def handler(context, state, data): ...

        return self.app._routes[0]["selector"]

    def test_event_matches_team_archived(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamArchived"},
                )
            )
            is True
        )

    def test_event_matches_team_renamed(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamRenamed"},
                )
            )
            is True
        )

    def test_event_matches_team_deleted(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamDeleted"},
                )
            )
            is True
        )

    def test_event_matches_team_hard_deleted(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamHardDeleted"},
                )
            )
            is True
        )

    def test_event_matches_team_restored(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamRestored"},
                )
            )
            is True
        )

    def test_event_matches_team_unarchived(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamUnarchived"},
                )
            )
            is True
        )

    def test_event_no_match_non_team_event(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "membersAdded"},
                )
            )
            is False
        )

    def test_event_requires_msteams_channel(self):
        selector = self._selector()
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

    def test_event_requires_conversation_update(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.message,
                    channel_data={"eventType": "teamArchived"},
                )
            )
            is False
        )

    def test_event_is_not_invoke(self):
        @self.ext.teams.event()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is False


class TestTeamDirectDecoratorStyle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_archived_direct(self):
        @self.ext.teams.archived  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_deleted_direct(self):
        @self.ext.teams.deleted  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_hard_deleted_direct(self):
        @self.ext.teams.hard_deleted  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_renamed_direct(self):
        @self.ext.teams.renamed  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_restored_direct(self):
        @self.ext.teams.restored  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_unarchived_direct(self):
        @self.ext.teams.unarchived  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None
