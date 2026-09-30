# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsTurnContext helpers that can be exercised without a live adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from .helpers import _make_context, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_agents.activity import (
        Activity,
        ActivityTreatment,
        ActivityTreatmentTypes,
        ActivityTypes,
        ChannelAccount,
        ConversationAccount,
        Entity,
        ResourceResponse,
        RoleTypes,
    )

    from microsoft_agents.hosting.msteams import TeamsActivity, TeamsTurnContext
    from microsoft_agents.hosting.msteams.models import QuotedReply, QuotedReplyData


class TestSendTargetedActivity:
    @staticmethod
    def _make_context(response: ResourceResponse) -> TeamsTurnContext:
        context = object.__new__(TeamsTurnContext)
        context.send_activity = AsyncMock(return_value=response)
        return context

    @staticmethod
    def _targeted_treatments(activity: Activity) -> list[Entity]:
        return [
            entity
            for entity in activity.entities or []
            if getattr(entity, "treatment", None) == ActivityTreatmentTypes.TARGETED
        ]

    @pytest.mark.asyncio
    async def test_sends_string_as_targeted_message_to_recipient_id(self):
        response = ResourceResponse(id="activity-id")
        context = self._make_context(response)

        result = await context.send_targeted_activity("hello", "user-id")

        assert result is response
        context.send_activity.assert_awaited_once()
        activity = context.send_activity.await_args.args[0]
        assert activity.type == ActivityTypes.message
        assert activity.text == "hello"
        assert activity.recipient == ChannelAccount(id="user-id", role=RoleTypes.user)
        assert len(self._targeted_treatments(activity)) == 1

    @pytest.mark.asyncio
    async def test_sends_activity_to_channel_account_without_losing_entities(self):
        response = ResourceResponse(id="activity-id")
        context = self._make_context(response)
        recipient = ChannelAccount(id="user-id", name="User")
        mention = Entity(type="mention")
        activity = Activity(
            type=ActivityTypes.message,
            text="hello",
            entities=[mention],
        )

        result = await context.send_targeted_activity(activity, recipient)

        assert result is response
        context.send_activity.assert_awaited_once_with(activity)
        assert activity.recipient == recipient
        assert mention in activity.entities
        assert len(self._targeted_treatments(activity)) == 1

    @pytest.mark.asyncio
    async def test_keeps_only_one_targeted_treatment(self):
        context = self._make_context(ResourceResponse())
        recipient = ChannelAccount(id="user-id")
        activity = Activity(
            type=ActivityTypes.message,
            entities=[
                ActivityTreatment(treatment=ActivityTreatmentTypes.TARGETED),
                Entity(type="mention"),
                ActivityTreatment(treatment=ActivityTreatmentTypes.TARGETED),
            ],
        )

        await context.send_targeted_activity(activity, recipient)

        assert Entity(type="mention") in activity.entities
        assert len(self._targeted_treatments(activity)) == 1


class TestPromptPreview:
    @pytest.mark.asyncio
    async def test_send_activity_uses_targeted_inbound_message_metadata(self):
        original = _make_context(ActivityTypes.message)
        original.activity.id = "inbound-message"
        original.activity.conversation = ConversationAccount(id="conversation-id")
        original.activity.recipient = ChannelAccount.model_validate(
            {"id": "agent-id", "isTargeted": True}
        )

        context = object.__new__(TeamsTurnContext)
        context._original = original
        context._teams_activity = original.activity

        response = TeamsActivity(
            type=ActivityTypes.message,
            text='<quoted messageId="quoted-message"/> response',
            entities=[
                QuotedReply(quoted_reply=QuotedReplyData(message_id="quoted-message"))
            ],
        )

        await context.send_activity(response)

        sent = original.adapter.sent_activities[0]
        assert sent.text == "response"
        assert not [
            entity for entity in sent.entities if entity.type.lower() == "quotedreply"
        ]
        targeted_message_info = [
            entity
            for entity in sent.entities
            if entity.type.lower() == "targetedmessageinfo"
        ]
        assert len(targeted_message_info) == 1
        assert targeted_message_info[0].message_id == "inbound-message"
