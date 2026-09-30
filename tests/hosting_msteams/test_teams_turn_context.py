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
    from microsoft_agents.hosting.msteams.models import (
        QuotedReply,
        QuotedReplyData,
        TargetedMessageInfo,
    )


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
    @staticmethod
    def _make_real_context(
        *,
        targeted: bool,
        activity_id: str = "inbound-message",
    ) -> tuple[TeamsTurnContext, object]:
        original = _make_context(ActivityTypes.message)
        original.activity.id = activity_id
        original.activity.conversation = ConversationAccount(id="conversation-id")
        recipient_data = {"id": "agent-id"}
        if targeted:
            recipient_data["isTargeted"] = True
        original.activity.recipient = ChannelAccount.model_validate(recipient_data)

        context = object.__new__(TeamsTurnContext)
        context._original = original
        context._teams_activity = original.activity
        return context, original.adapter

    @pytest.mark.asyncio
    async def test_send_activity_uses_targeted_inbound_message_metadata(self):
        context, adapter = self._make_real_context(targeted=True)

        response = TeamsActivity(
            type=ActivityTypes.message,
            text='<quoted messageId="quoted-message"/> response',
            entities=[
                QuotedReply(quoted_reply=QuotedReplyData(message_id="quoted-message"))
            ],
        )

        await context.send_activity(response)

        sent = adapter.sent_activities[0]
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

    @pytest.mark.asyncio
    async def test_send_string_adds_prompt_preview_for_targeted_inbound(self):
        context, adapter = self._make_real_context(targeted=True)

        await context.send_activity("response")

        sent = adapter.sent_activities[0]
        targeted_message_info = [
            entity
            for entity in sent.entities
            if entity.type.lower() == "targetedmessageinfo"
        ]
        assert len(targeted_message_info) == 1
        assert targeted_message_info[0].message_id == "inbound-message"

    @pytest.mark.asyncio
    async def test_send_activity_does_not_add_prompt_preview_for_regular_inbound(self):
        context, adapter = self._make_real_context(targeted=False)

        await context.send_activity(
            Activity(type=ActivityTypes.message, text="response")
        )

        sent = adapter.sent_activities[0]
        assert not [
            entity
            for entity in sent.entities or []
            if entity.type.lower() == "targetedmessageinfo"
        ]

    @pytest.mark.asyncio
    async def test_send_activities_adds_prompt_preview_to_each_message(self):
        context, adapter = self._make_real_context(targeted=True)

        await context.send_activities(
            [
                Activity(type=ActivityTypes.message, text="first"),
                Activity(type=ActivityTypes.message, text="second"),
            ]
        )

        assert len(adapter.sent_activities) == 2
        for sent in adapter.sent_activities:
            targeted_message_info = [
                entity
                for entity in sent.entities
                if entity.type.lower() == "targetedmessageinfo"
            ]
            assert len(targeted_message_info) == 1
            assert targeted_message_info[0].message_id == "inbound-message"

    @pytest.mark.asyncio
    async def test_send_activity_preserves_explicit_prompt_preview_metadata(self):
        context, adapter = self._make_real_context(targeted=True)
        response = Activity(
            type=ActivityTypes.message,
            text="response",
            entities=[TargetedMessageInfo(message_id="explicit-message")],
        )

        await context.send_activity(response)

        sent = adapter.sent_activities[0]
        targeted_message_info = [
            entity
            for entity in sent.entities
            if entity.type.lower() == "targetedmessageinfo"
        ]
        assert len(targeted_message_info) == 1
        assert targeted_message_info[0].message_id == "explicit-message"
