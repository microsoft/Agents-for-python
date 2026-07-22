# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity.card_action import CardAction
import pytest

from microsoft_agents.activity import (
    Activity,
    AttachmentLayoutTypes,
    Attachment,
    ChannelAccount,
    DeliveryModes,
    Entity,
    InputHints,
    Mention,
    SuggestedActions,
    TextFormatTypes,
)


class TestActivityFluentBuilders:
    def test_fluent_setters_chain_and_set_properties(self):
        activity = (
            Activity.create_message_activity()
            .with_text("hello")
            .with_speak("hello there")
            .with_input_hint(InputHints.expecting_input)
            .with_summary("a summary")
            .with_locale("en-US")
            .with_text_format(TextFormatTypes.markdown)
            .with_attachment_layout(AttachmentLayoutTypes.carousel)
            .with_delivery_mode(DeliveryModes.normal)
            .with_name("theName")
            .with_value("theValue", "theValueType")
        )

        assert activity.text == "hello"
        assert activity.speak == "hello there"
        assert activity.input_hint == InputHints.expecting_input
        assert activity.summary == "a summary"
        assert activity.locale == "en-US"
        assert activity.text_format == TextFormatTypes.markdown
        assert activity.attachment_layout == AttachmentLayoutTypes.carousel
        assert activity.delivery_mode == DeliveryModes.normal
        assert activity.name == "theName"
        assert activity.value == "theValue"
        assert activity.value_type == "theValueType"

    def test_with_value_without_value_type(self):
        activity = Activity.create_message_activity().with_value("theValue")

        assert activity.value == "theValue"
        assert activity.value_type is None

    def test_with_suggested_actions(self):
        actions = SuggestedActions(
            to=["u1"],
            actions=[CardAction(type="imBack", title="Click Me", value="clicked")],
        )
        activity = Activity.create_message_activity().with_suggested_actions(actions)

        assert activity.suggested_actions is actions

    def test_add_text_appends(self):
        activity = Activity.create_message_activity().with_text("foo")
        activity.add_text("bar")

        assert activity.text == "foobar"

    def test_add_text_appends_when_text_is_none(self):
        activity = Activity.create_message_activity()
        activity.add_text("bar")

        assert activity.text == "bar"

    def test_add_attachment_adds_attachments(self):
        activity = Activity.create_message_activity().add_attachment(
            Attachment(content_type="a"), Attachment(content_type="b")
        )

        assert len(activity.attachments) == 2
        assert activity.attachments[0].content_type == "a"
        assert activity.attachments[1].content_type == "b"

    def test_add_entity_adds_entities(self):
        activity = Activity.create_message_activity().add_entity(Entity(type="myType"))

        assert len(activity.entities) == 1
        assert activity.entities[0].type == "myType"


class TestSuggestedActionsBuilders:
    def test_suggested_actions_fluent_adders(self):
        suggested = (
            SuggestedActions()
            .add_recipients("r1", "r2")
            .add_action(CardAction(type="imBack", title="a"))
            .add_actions(
                CardAction(type="imBack", title="b"),
                CardAction(type="imBack", title="c"),
            )
        )

        assert suggested.to == ["r1", "r2"]
        assert len(suggested.actions) == 3
        assert suggested.actions[0].title == "a"
        assert suggested.actions[2].title == "c"


class TestActivityMentions:
    def test_add_mention_adds_entity_and_text(self):
        account = ChannelAccount(id="u1", name="User One")
        activity = (
            Activity.create_message_activity().with_text("hi").add_mention(account)
        )

        assert activity.text == "<at>User One</at> hi"
        mention = activity.entities[0]
        assert isinstance(mention, Mention)
        assert mention.mentioned.id == "u1"
        assert mention.text == "<at>User One</at>"

    def test_add_mention_can_skip_text(self):
        account = ChannelAccount(id="u1", name="User One")
        activity = (
            Activity.create_message_activity()
            .with_text("hi")
            .add_mention(account, text="Custom", add_text=False)
        )

        assert activity.text == "hi"
        mention = activity.entities[0]
        assert isinstance(mention, Mention)
        assert mention.text == "<at>Custom</at>"

    def test_get_account_mention_returns_match(self):
        account = ChannelAccount(id="u1", name="User One")
        activity = Activity.create_message_activity().add_mention(account)

        mention = activity.get_account_mention("u1")
        assert mention is not None
        assert mention.mentioned.id == "u1"

        assert activity.get_account_mention("other") is None
        assert activity.get_account_mention(None) is None

    def test_is_recipient_mentioned(self):
        recipient = ChannelAccount(id="bot", name="Bot")
        activity = Activity.create_message_activity()
        activity.recipient = recipient

        assert activity.is_recipient_mentioned() is False

        activity.add_mention(recipient)
        assert activity.is_recipient_mentioned() is True

    def test_remove_recipient_mention(self):
        recipient = ChannelAccount(id="bot", name="Bot")
        activity = Activity.create_message_activity()
        activity.recipient = recipient
        activity.with_text("Hi Agent").add_mention(recipient)

        assert activity.text == "<at>Bot</at> Hi Agent"

        result = activity.remove_recipient_mention()
        assert result == "Hi Agent"
        assert activity.text == "Hi Agent"


class TestActivityTargeting:
    def test_make_targeted_activity_sets_treatment(self):
        recipient = ChannelAccount(id="bot", name="Bot")
        activity = Activity.create_message_activity()
        activity.recipient = recipient

        assert activity.is_targeted_activity() is False

        activity.make_targeted_activity()
        assert activity.is_targeted_activity() is True

    def test_make_targeted_activity_uses_user_argument(self):
        user = ChannelAccount(id="u1", name="User One")
        activity = Activity.create_message_activity().make_targeted_activity(user)

        assert activity.is_targeted_activity() is True
        assert activity.recipient.id == "u1"

    def test_make_targeted_activity_is_idempotent(self):
        recipient = ChannelAccount(id="bot", name="Bot")
        activity = Activity.create_message_activity()
        activity.recipient = recipient
        activity.make_targeted_activity()
        activity.make_targeted_activity()

        treatments = [e for e in activity.entities if e.type == "activityTreatment"]
        assert len(treatments) == 1

    def test_make_targeted_activity_raises_without_recipient_or_user(self):
        activity = Activity.create_message_activity()

        with pytest.raises(ValueError):
            activity.make_targeted_activity()


class TestActivityTypePredicates:
    def test_is_type_helpers(self):
        assert Activity.create_message_activity().is_message() is True
        assert Activity.create_typing_activity().is_typing() is True
        assert Activity.create_event_activity().is_event() is True
        assert Activity.create_invoke_activity().is_invoke() is True
        assert (
            Activity.create_conversation_update_activity().is_conversation_update()
            is True
        )
        assert (
            Activity.create_end_of_conversation_activity().is_end_of_conversation()
            is True
        )
        assert Activity.create_handoff_activity().is_handoff() is True
        assert Activity.create_message_activity().is_invoke() is False

    def test_is_trace_command_predicates(self):
        assert Activity(type="trace").is_trace() is True
        assert Activity(type="command").is_command() is True
        assert Activity(type="commandResult").is_command_result() is True
        assert Activity(type="message").is_command() is False
