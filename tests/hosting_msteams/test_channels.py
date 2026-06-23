# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension.channels (channel and membership conversation update events)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.activity import ActivityTypes

from .helpers import _make_app, _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_agents.hosting.teams import TeamsAgentExtension


class TestChannelLifecycle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_created_selector(self):
        @self.ext.channels.created()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelCreated"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelDeleted"},
                )
            )
            is False
        )

    def test_deleted_selector(self):
        @self.ext.channels.deleted()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelDeleted"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelCreated"},
                )
            )
            is False
        )

    def test_renamed_selector(self):
        @self.ext.channels.renamed()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelRenamed"},
                )
            )
            is True
        )

    def test_restored_selector(self):
        @self.ext.channels.restored()
        async def handler(context, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelRestored"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelRenamed"},
                )
            )
            is False
        )

    def test_shared_selector(self):
        @self.ext.channels.shared()
        async def handler(context, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelShared"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelUnshared"},
                )
            )
            is False
        )

    def test_unshared_selector(self):
        @self.ext.channels.unshared()
        async def handler(context, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelUnshared"},
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelShared"},
                )
            )
            is False
        )

    def test_channel_event_requires_msteams_channel(self):
        @self.ext.channels.created()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_id="webchat",
                    channel_data={"eventType": "channelCreated"},
                )
            )
            is False
        )

    def test_channel_event_is_not_invoke(self):
        @self.ext.channels.created()
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["is_invoke"] is False


class TestChannelMembers:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_members_added_selector(self):
        @self.ext.channels.members_added()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        assert (
            selector(
                _make_context(ActivityTypes.conversation_update, members_added=[member])
            )
            is True
        )
        assert (
            selector(_make_context(ActivityTypes.conversation_update, members_added=[]))
            is False
        )

    def test_members_added_requires_msteams_channel(self):
        @self.ext.channels.members_added()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_id="webchat",
                    members_added=[member],
                )
            )
            is False
        )

    def test_members_removed_selector(self):
        @self.ext.channels.members_removed()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update, members_removed=[member]
                )
            )
            is True
        )
        assert (
            selector(
                _make_context(ActivityTypes.conversation_update, members_removed=[])
            )
            is False
        )

    def test_members_removed_requires_msteams_channel(self):
        @self.ext.channels.members_removed()
        async def handler(ctx, state, data): ...

        selector = self.app._routes[0]["selector"]
        member = MagicMock()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_id="webchat",
                    members_removed=[member],
                )
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_members_added_handler_passes_channel_data(self):
        from microsoft_teams.api.models.channel_data import ChannelData

        user_handler = AsyncMock()

        @self.ext.channels.members_added()
        async def handler(ctx, state, data):
            await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        member = MagicMock()
        ctx = _make_context(
            ActivityTypes.conversation_update,
            members_added=[member],
            channel_data={"eventType": "membersAdded"},
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], ChannelData)

    @pytest.mark.asyncio
    async def test_members_removed_handler_passes_channel_data(self):
        from microsoft_teams.api.models.channel_data import ChannelData

        user_handler = AsyncMock()

        @self.ext.channels.members_removed()
        async def handler(ctx, state, data):
            await user_handler(ctx, state, data)

        route_handler = self.app._routes[0]["handler"]
        member = MagicMock()
        ctx = _make_context(
            ActivityTypes.conversation_update,
            members_removed=[member],
            channel_data={"eventType": "membersRemoved"},
        )
        await route_handler(ctx, MagicMock())
        assert isinstance(user_handler.call_args[0][2], ChannelData)

    @pytest.mark.asyncio
    async def test_members_added_raises_when_channel_data_missing(self):
        @self.ext.channels.members_added()
        async def handler(ctx, state, data): ...

        route_handler = self.app._routes[0]["handler"]
        member = MagicMock()
        ctx = _make_context(ActivityTypes.conversation_update, members_added=[member])
        with pytest.raises(ValueError, match="channel_data"):
            await route_handler(ctx, MagicMock())


class TestChannelEvent:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def _selector(self):
        @self.ext.channels.event()
        async def handler(context, state, data): ...

        return self.app._routes[0]["selector"]

    def test_event_matches_channel_created(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelCreated"},
                )
            )
            is True
        )

    def test_event_matches_channel_deleted(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelDeleted"},
                )
            )
            is True
        )

    def test_event_matches_channel_renamed(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelRenamed"},
                )
            )
            is True
        )

    def test_event_matches_channel_restored(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelRestored"},
                )
            )
            is True
        )

    def test_event_matches_channel_shared(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelShared"},
                )
            )
            is True
        )

    def test_event_matches_channel_unshared(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "channelUnshared"},
                )
            )
            is True
        )

    def test_event_no_match_non_channel_event(self):
        selector = self._selector()
        assert (
            selector(
                _make_context(
                    ActivityTypes.conversation_update,
                    channel_data={"eventType": "teamArchived"},
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
                    channel_data={"eventType": "channelCreated"},
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
                    channel_data={"eventType": "channelCreated"},
                )
            )
            is False
        )

    def test_event_is_not_invoke(self):
        @self.ext.channels.event()
        async def handler(context, state, data): ...

        assert self.app._routes[0]["is_invoke"] is False


class TestChannelDirectDecoratorStyle:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_created_direct(self):
        @self.ext.channels.created  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_deleted_direct(self):
        @self.ext.channels.deleted  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_renamed_direct(self):
        @self.ext.channels.renamed  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_restored_direct(self):
        @self.ext.channels.restored  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_shared_direct(self):
        @self.ext.channels.shared  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_unshared_direct(self):
        @self.ext.channels.unshared  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_event_direct(self):
        @self.ext.channels.event  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_members_added_direct(self):
        @self.ext.channels.members_added  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None

    def test_members_removed_direct(self):
        @self.ext.channels.members_removed  # type: ignore[arg-type]
        async def handler(ctx, state, data): ...

        assert self.app._routes[0]["selector"] is not None
