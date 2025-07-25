import pytest
from typing import Callable, List

from microsoft.agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    Entity,
    ResourceResponse,
)
from microsoft.agents.hosting.core import ChannelAdapter, MessageFactory, TurnContext

activity_data = {
    "type": "message",
    "id": "1234",
    "text": "test",
    "from_property": ChannelAccount(id="user", name="User Name"),
    "recipient": ChannelAccount(id="bot", name="Bot Name"),
    "conversation": ConversationAccount(id="convo", name="Convo Name"),
    "channel_id": "UnitTest",
    "locale": "en-uS",
    "service_url": "https://example.org",
}

ACTIVITY = Activity(**activity_data)


class MockSimpleAdapter(ChannelAdapter):
    async def send_activities(self, context, activities) -> List[ResourceResponse]:
        responses = []
        assert context is not None
        assert activities is not None
        assert isinstance(activities, list)
        assert activities
        for idx, activity in enumerate(activities):  # pylint: disable=unused-variable
            assert isinstance(activity, Activity)
            assert activity.type == "message" or activity.type == ActivityTypes.trace
            responses.append(ResourceResponse(id="5678"))
        return responses

    async def update_activity(self, context, activity):
        assert context is not None
        assert activity is not None
        assert activity.id is not None
        return ResourceResponse(id=activity.id)

    async def delete_activity(self, context, reference):
        assert context is not None
        assert reference is not None
        assert reference.activity_id == ACTIVITY.id


class TestTurnContext:
    def test_should_create_context_with_request_and_adapter(self):
        TurnContext(MockSimpleAdapter(), ACTIVITY)

    def test_should_not_create_context_without_request(self):
        try:
            TurnContext(MockSimpleAdapter(), None)
        except TypeError:
            pass
        except Exception as error:
            raise error

    def test_should_not_create_context_without_adapter(self):
        try:
            TurnContext(None, ACTIVITY)
        except TypeError:
            pass
        except Exception as error:
            raise error

    def test_should_create_context_with_older_context(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        TurnContext(context)

    def test_copy_to_should_copy_all_references(self):
        # pylint: disable=protected-access
        old_adapter = MockSimpleAdapter()
        old_activity = Activity(id="2", type="message", text="test copy")
        old_context = TurnContext(old_adapter, old_activity)
        old_context.responded = True

        async def send_activities_handler(context, activities, next_handler):
            assert context is not None
            assert activities is not None
            assert next_handler is not None
            await next_handler

        async def delete_activity_handler(context, reference, next_handler):
            assert context is not None
            assert reference is not None
            assert next_handler is not None
            await next_handler

        async def update_activity_handler(context, activity, next_handler):
            assert context is not None
            assert activity is not None
            assert next_handler is not None
            await next_handler

        old_context.on_send_activities(send_activities_handler)
        old_context.on_delete_activity(delete_activity_handler)
        old_context.on_update_activity(update_activity_handler)

        adapter = MockSimpleAdapter()
        new_context = TurnContext(adapter, ACTIVITY)
        assert not new_context._on_send_activities  # pylint: disable=protected-access
        assert not new_context._on_update_activity  # pylint: disable=protected-access
        assert not new_context._on_delete_activity  # pylint: disable=protected-access

        old_context.copy_to(new_context)

        assert new_context.adapter == old_adapter
        assert new_context.activity == old_activity
        assert new_context.responded is True
        assert (
            len(new_context._on_send_activities) == 1
        )  # pylint: disable=protected-access
        assert (
            len(new_context._on_update_activity) == 1
        )  # pylint: disable=protected-access
        assert (
            len(new_context._on_delete_activity) == 1
        )  # pylint: disable=protected-access

    def test_responded_should_be_automatically_set_to_false(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        assert context.responded is False

    def test_should_be_able_to_set_responded_to_true(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        assert context.responded is False
        context.responded = True
        assert context.responded

    def test_should_not_be_able_to_set_responded_to_false(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        try:
            context.responded = False
        except ValueError:
            pass
        except Exception as error:
            raise error

    @pytest.mark.asyncio
    async def test_should_call_on_delete_activity_handlers_before_deletion(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called = False

        async def delete_handler(context, reference, next_handler_coroutine):
            nonlocal called
            called = True
            assert reference is not None
            assert context is not None
            assert reference.activity_id == "1234"
            await next_handler_coroutine()

        context.on_delete_activity(delete_handler)
        await context.delete_activity(ACTIVITY.id)
        assert called is True

    @pytest.mark.asyncio
    async def test_should_call_multiple_on_delete_activity_handlers_in_order(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called_first = False
        called_second = False

        async def first_delete_handler(context, reference, next_handler_coroutine):
            nonlocal called_first, called_second
            assert (
                called_first is False
            ), "called_first should not be True before first_delete_handler is called."
            called_first = True
            assert (
                called_second is False
            ), "Second on_delete_activity handler was called before first."
            assert reference is not None
            assert context is not None
            assert reference.activity_id == "1234"
            await next_handler_coroutine()

        async def second_delete_handler(context, reference, next_handler_coroutine):
            nonlocal called_first, called_second
            assert called_first
            assert (
                called_second is False
            ), "called_second was set to True before second handler was called."
            called_second = True
            assert reference is not None
            assert context is not None
            assert reference.activity_id == "1234"
            await next_handler_coroutine()

        context.on_delete_activity(first_delete_handler)
        context.on_delete_activity(second_delete_handler)
        await context.delete_activity(ACTIVITY.id)
        assert called_first is True
        assert called_second is True

    @pytest.mark.asyncio
    async def test_should_call_send_on_activities_handler_before_send(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called = False

        async def send_handler(context, activities, next_handler_coroutine):
            nonlocal called
            called = True
            assert activities is not None
            assert context is not None
            assert not activities[0].id
            await next_handler_coroutine()

        context.on_send_activities(send_handler)
        await context.send_activity(ACTIVITY)
        assert called is True

    @pytest.mark.asyncio
    async def test_should_call_on_update_activity_handler_before_update(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called = False

        async def update_handler(context, activity, next_handler_coroutine):
            nonlocal called
            called = True
            assert activity is not None
            assert context is not None
            assert activity.id == "1234"
            await next_handler_coroutine()

        context.on_update_activity(update_handler)
        await context.update_activity(ACTIVITY)
        assert called is True

    @pytest.mark.asyncio
    async def test_update_activity_should_apply_conversation_reference(self):
        activity_id = "activity ID"
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called = False

        async def update_handler(context, activity, next_handler_coroutine):
            nonlocal called
            called = True
            assert context is not None
            assert activity.id == activity_id
            assert activity.conversation.id == ACTIVITY.conversation.id
            await next_handler_coroutine()

        context.on_update_activity(update_handler)
        new_activity = MessageFactory.text("test text")
        new_activity.id = activity_id
        update_result = await context.update_activity(new_activity)
        assert called is True
        assert update_result.id == activity_id

    def test_get_conversation_reference_should_return_valid_reference(self):
        reference = ACTIVITY.get_conversation_reference()

        assert reference.activity_id == ACTIVITY.id
        assert reference.user == ACTIVITY.from_property
        assert reference.agent == ACTIVITY.recipient
        assert reference.conversation == ACTIVITY.conversation
        assert reference.channel_id == ACTIVITY.channel_id
        assert reference.locale == ACTIVITY.locale
        assert reference.service_url == ACTIVITY.service_url

    def test_apply_conversation_reference_should_return_prepare_reply_when_is_incoming_is_false(
        self,
    ):
        reference = ACTIVITY.get_conversation_reference()
        reply = TurnContext.apply_conversation_reference(
            Activity(type="message", text="reply"), reference
        )

        assert reply.recipient == ACTIVITY.from_property
        assert reply.from_property == ACTIVITY.recipient
        assert reply.conversation == ACTIVITY.conversation
        assert reply.locale == ACTIVITY.locale
        assert reply.service_url == ACTIVITY.service_url
        assert reply.channel_id == ACTIVITY.channel_id

    def test_apply_conversation_reference_when_is_incoming_is_true_should_not_prepare_a_reply(
        self,
    ):
        reference = ACTIVITY.get_conversation_reference()
        reply = TurnContext.apply_conversation_reference(
            Activity(type="message", text="reply"), reference, True
        )

        assert reply.recipient == ACTIVITY.recipient
        assert reply.from_property == ACTIVITY.from_property
        assert reply.conversation == ACTIVITY.conversation
        assert reply.locale == ACTIVITY.locale
        assert reply.service_url == ACTIVITY.service_url
        assert reply.channel_id == ACTIVITY.channel_id

    @pytest.mark.asyncio
    async def test_should_get_conversation_reference_using_get_reply_conversation_reference(
        self,
    ):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        reply = await context.send_activity("test")

        assert reply is not None
        assert reply.id, "reply has an id"

        reference = TurnContext.get_reply_conversation_reference(
            context.activity, reply
        )

        assert reference.activity_id, "reference has an activity id"
        assert (
            reference.activity_id == reply.id
        ), "reference id matches outgoing reply id"

    def test_should_remove_at_mention_from_activity(self):
        activity = Activity(
            type="message",
            text="<at>TestOAuth619</at> test activity",
            recipient=ChannelAccount(id="TestOAuth619"),
            entities=[
                # Mentions are likely entities due to serialization
                Entity(
                    type="mention",
                    text="<at>TestOAuth619</at>",
                    mentioned={"name": "Bot", "id": "TestOAuth619"},
                )
            ],
        )

        text = TurnContext.remove_recipient_mention(activity)

        assert text == " test activity"
        assert activity.text == " test activity"

    def test_should_remove_at_mention_with_regex_characters(self):
        activity = Activity(
            type="message",
            text="<at>Test (*.[]$%#^&?)</at> test activity",
            recipient=ChannelAccount(id="Test (*.[]$%#^&?)"),
            entities=[
                # mentions are likely entities due to serialization
                Entity(
                    type="mention",
                    text="<at>Test (*.[]$%#^&?)</at>",
                    mentioned={"name": "Bot", "id": "Test (*.[]$%#^&?)"},
                )
            ],
        )

        text = TurnContext.remove_recipient_mention(activity)

        assert text == " test activity"
        assert activity.text == " test activity"

    def test_should_remove_custom_mention_from_activity(self):
        activity = Activity(
            text="Hallo",
            text_format="plain",
            type="message",
            timestamp="2025-03-11T14:16:47.0093935Z",
            id="1741702606984",
            channel_id="msteams",
            service_url="https://smba.trafficmanager.net/emea/REDACTED/",
            from_property=ChannelAccount(
                id="29:1J-K4xVh-sLpdwQ-R5GkOZ_TB0W3ec_37p710aH8qe8bITA0zxdgIGc9l-MdDdkdE_jasSfNOeWXyyL1nsrHtBQ",
                name="",
                aad_object_id="REDACTED",
            ),
            conversation=ConversationAccount(
                is_group=True,
                conversation_type="groupChat",
                tenant_id="REDACTED",
                id="19:Ql86tXNM2lTBXNKJdqKdwIF9ltGZwpvluLvnJdA0tmg1@thread.v2",
            ),
            recipient=ChannelAccount(
                id="28:c5d5fb56-a1a4-4467-a7a3-1b37905498a0", name="Azure AI Agent"
            ),
            entities=[
                # mentions are likely entities due to serialization
                Entity(
                    type="mention",
                    mentioned={
                        "id": "28:c5d5fb56-a1a4-4467-a7a3-1b37905498a0",
                        "name": "Custom Agent",
                    },
                )
            ],
            channel_data={"tenant": {"id": "REDACTED"}, "productContext": "COPILOT"},
        )

        text = TurnContext.remove_mention_text(activity, activity.recipient.id)

        assert text == "Hallo"
        assert activity.text == "Hallo"

    @pytest.mark.asyncio
    async def test_should_send_a_trace_activity(self):
        context = TurnContext(MockSimpleAdapter(), ACTIVITY)
        called = False

        #  pylint: disable=unused-argument
        async def aux_func(
            ctx: TurnContext, activities: List[Activity], next: Callable
        ):
            nonlocal called
            called = True
            assert isinstance(activities, list), "activities not array."
            assert len(activities) == 1, "invalid count of activities."
            assert activities[0].type == ActivityTypes.trace, "type wrong."
            assert activities[0].name == "name-text", "name wrong."
            assert activities[0].value == "value-text", "value worng."
            assert activities[0].value_type == "valueType-text", "valeuType wrong."
            assert activities[0].label == "label-text", "label wrong."
            return []

        context.on_send_activities(aux_func)
        await context.send_trace_activity(
            "name-text", "value-text", "valueType-text", "label-text"
        )
        assert called
