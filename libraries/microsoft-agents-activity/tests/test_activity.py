from microsoft_agents.activity.entity import mention
import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Entity,
    Mention,
    ResourceResponse,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    DeliveryModes,
    Attachment,
    GeoCoordinates,
    AIEntity,
    Place,
    Thing,
)

from .activity_data.activity_test_data import MyChannelData
from .activity_tools.testing_activity import create_test_activity


def helper_validate_recipient_and_from(
    activity: Activity, create_recipient: bool, create_from: bool
):
    if create_recipient:
        assert activity.from_property.id == "ChannelAccount_Id_2"
        assert activity.from_property.name == "ChannelAccount_Name_2"
    else:
        assert activity.from_property.id is None
        assert activity.from_property.name is None

    if create_from:
        assert activity.recipient.id == "ChannelAccount_Id_1"
        assert activity.recipient.name == "ChannelAccount_Name_1"
    else:
        assert activity.recipient.id is None
        assert activity.recipient.name is None


def helper_get_expected_try_get_channel_data_result(channel_data) -> bool:
    return isinstance(channel_data, dict) or isinstance(channel_data, MyChannelData)


class TestActivityConversationOps:

    @pytest.fixture
    def activity(self):
        return create_test_activity("en-us")

    def test_get_conversation_reference(self, activity):
        conversation_reference = activity.get_conversation_reference()

        assert activity.id == conversation_reference.activity_id
        assert activity.from_property.id == conversation_reference.user.id
        assert activity.recipient.id == conversation_reference.agent.id
        assert activity.conversation.id == conversation_reference.conversation.id
        assert activity.channel_id == conversation_reference.channel_id
        assert activity.locale == conversation_reference.locale
        assert activity.service_url == conversation_reference.service_url

    def test_get_reply_conversation_reference(self, activity):
        reply = ResourceResponse(id="1234")
        conversation_reference = activity.get_reply_conversation_reference(reply)

        assert reply.id == conversation_reference.activity_id
        assert activity.from_property.id == conversation_reference.user.id
        assert activity.recipient.id == conversation_reference.agent.id
        assert activity.conversation.id == conversation_reference.conversation.id
        assert activity.channel_id == conversation_reference.channel_id
        assert activity.locale == conversation_reference.locale
        assert activity.service_url == conversation_reference.service_url

    def remove_recipient_mention_for_teams(self, activity):
        activity.text = "<at>firstName</a> lastName\n"
        expected_stripped_name = "lastName"

        mention = Mention(
            mentioned=ChannelAccount(id=activity.recipient.id, name="firstName"),
            text=None,
        )
        lst = []

        output = mention.model_dump()
        entity = Entity(**output)

        lst.append(entity)
        activity.entities = lst

        stripped_activity_text = activity.remove_recipient_mention()
        assert stripped_activity_text == expected_stripped_name

    def remove_recipient_mention_for_non_teams_scenario(self, activity):
        activity.text = "<at>firstName</a> lastName\n"
        expected_stripped_name = "lastName"

        mention = Mention(
            ChannelAccount(id=activity.recipient.id, name="<at>firstName</a>"),
            text="<at>firstName</at>",
        )
        lst = []

        output = mention.model_dump()
        entity = Entity(**output)

        lst.append(entity)
        activity.entities = lst

        stripped_activity_text = activity.remove_recipient_mention()
        assert stripped_activity_text == expected_stripped_name

    def test_apply_conversation_reference_is_incoming(self):
        activity = create_test_activity("en-uS")  # on purpose
        conversation_reference = ConversationReference(
            channel_id="cr_123",
            service_url="cr_serviceUrl",
            conversation=ConversationAccount(id="cr_456"),
            user=ChannelAccount(id="cr_abc"),
            agent=ChannelAccount(id="cr_def"),
            activity_id="cr_12345",
            locale="en-us",
            # delivery_mode = DeliveryModes.expect_replies
        )

        activity_to_send = activity.apply_conversation_reference(
            conversation_reference, is_incoming=True
        )
        conversation_reference = activity_to_send.get_conversation_reference()

        assert conversation_reference.channel_id == activity.channel_id
        assert conversation_reference.service_url == activity.service_url
        assert conversation_reference.conversation.id == activity.conversation.id
        # assert conversation_reference.delivery_mode == activity.delivery_mode robrandao: TODO
        assert conversation_reference.user.id == activity.from_property.id
        assert conversation_reference.agent.id == activity.recipient.id
        assert conversation_reference.activity_id == activity.id
        assert activity.locale == activity_to_send.locale

    @pytest.mark.parametrize("locale", ["EN-US", "en-uS"])
    def test_apply_conversation_reference(self, locale):
        activity = create_test_activity(locale)
        conversation_reference = ConversationReference(
            channel_id="123",
            service_url="serviceUrl",
            conversation=ConversationAccount(id="456"),
            user=ChannelAccount(id="abc"),
            agent=ChannelAccount(id="def"),
            activity_id="12345",
            locale="en-us",
        )

        activity_to_send = activity.apply_conversation_reference(
            conversation_reference, is_incoming=False
        )

        assert conversation_reference.channel_id == activity.channel_id
        assert conversation_reference.service_url == activity.service_url
        assert conversation_reference.conversation.id == activity.conversation.id

        assert conversation_reference.agent.id == activity.from_property.id
        assert conversation_reference.user.id == activity.recipient.id

        if locale is None:
            assert conversation_reference.locale == activity_to_send.locale
        else:
            assert activity.locale == activity_to_send.locale

    @pytest.mark.parametrize(
        "value, value_type, create_recipient, create_from, label",
        [
            ["myValue", None, False, False, None],
            [None, None, False, False, None],
            [None, "myValueType", False, False, None],
            [None, None, True, False, None],
            [None, None, False, True, "testLabel"],
        ],
    )
    def test_create_trace(
        self, value, value_type, create_recipient, create_from, label
    ):
        activity = create_test_activity("en-us", create_recipient, create_from)
        trace = activity.create_trace("test", value, value_type, label)

        assert trace is not None
        assert trace.type == ActivityTypes.trace
        if value_type:
            assert trace.value_type == value_type
        elif value:
            assert trace.value_type == type(value).__name__
        else:
            assert trace.value_type is None
        assert trace.label == label
        assert trace.name == "test"

    @pytest.mark.parametrize(
        "activity_type, activity_type_name",
        [
            (ActivityTypes.end_of_conversation, "end_of_conversation"),
            (ActivityTypes.event, "event"),
            (ActivityTypes.handoff, "handoff"),
            (ActivityTypes.invoke, "invoke"),
            (ActivityTypes.message, "message"),
            (ActivityTypes.typing, "typing"),
        ],
    )
    def test_can_create_activities(self, activity_type, activity_type_name):
        create_activity_method = getattr(
            Activity, f"create_{activity_type_name}_activity"
        )
        activity = create_activity_method()
        expected_activity_type = activity_type

        assert activity is not None
        assert activity.type == expected_activity_type

        if expected_activity_type == ActivityTypes.message:
            assert activity.attachments is None
            assert activity.entities is None

    @pytest.mark.parametrize(
        "name, value_type, value, label",
        [["TestTrace", "NoneType", None, None], ["TestTrace", None, "TestValue", None]],
    )
    def test_create_trace_activity(self, name, value_type, value, label):
        activity = Activity.create_trace_activity(name, value, value_type, label)

        assert activity is not None
        assert activity.type == ActivityTypes.trace
        assert activity.name == name
        assert activity.value_type == type(value).__name__
        assert activity.value == value
        assert activity.label == label

    @pytest.mark.parametrize(
        "activity_locale, text, create_recipient, create_from, create_reply_locale",
        [
            ["en-uS", "response", False, True, None],
            ["en-uS", "response", False, False, None],
            [None, "", True, False, "en-us"],
            [None, None, True, True, None],
        ],
    )
    def test_can_create_reply_activity(
        self, activity_locale, text, create_recipient, create_from, create_reply_locale
    ):
        activity = create_test_activity(activity_locale, create_recipient, create_from)
        reply = activity.create_reply(text, locale=create_reply_locale)

        assert reply is not None
        assert reply.type == ActivityTypes.message
        assert reply.reply_to_id == "123"
        assert reply.service_url == "ServiceUrl123"
        assert reply.channel_id == "ChannelId123"
        assert reply.text == text or reply.text == ""
        assert reply.locale == activity_locale or create_reply_locale

        if create_recipient:
            assert reply.from_property.id == "ChannelAccount_Id_2"
            assert reply.from_property.name == "ChannelAccount_Name_2"
        else:
            assert reply.from_property is None

        if create_from:
            assert reply.recipient.id == "ChannelAccount_Id_1"
            assert reply.recipient.name == "ChannelAccount_Name_1"
        else:
            assert reply.recipient is None

    @pytest.fixture(params=[None, {}, MyChannelData()])
    def channel_data(self, request):
        return request.param

    @pytest.mark.parametrize(
        "activity, expected",
        [
            [Activity(type=ActivityTypes.message, text="Hello"), True],
            [Activity(type=ActivityTypes.message, text=" \n \t "), False],
            [Activity(type=ActivityTypes.message, text=" "), False],
            [
                Activity(type=ActivityTypes.message, attachments=[], summary="Summary"),
                True,
            ],
            [Activity(type=ActivityTypes.message, text=" ", summary="\t"), False],
            [Activity(type=ActivityTypes.message, summary="\t"), False],
            [
                Activity(
                    type=ActivityTypes.message,
                    text="\n",
                    summary="\n",
                    attachments=[Attachment(content_type="123")],
                ),
                True,
            ],
            [
                Activity(
                    type=ActivityTypes.message, text="\n", summary="\n", attachments=[]
                ),
                False,
            ],
            [
                Activity(
                    type=ActivityTypes.message,
                    text="\n",
                    summary="\t",
                    attachments=[],
                    channel_data=MyChannelData(),
                ),
                True,
            ],
            [
                Activity(
                    type=ActivityTypes.message,
                    text="\n",
                    summary=" wow ",
                    attachments=[],
                    channel_data=MyChannelData(),
                ),
                True,
            ],
            [
                Activity(
                    type=ActivityTypes.message,
                    text="huh ",
                    summary="\t",
                    attachments=[],
                    channel_data=MyChannelData(),
                ),
                True,
            ],
        ],
    )
    def test_has_content(self, activity, expected):
        assert activity.has_content() == expected

    @pytest.mark.parametrize(
        "service_url, expected",
        [
            ["https://localhost", False],
            ["microsoft.com", True],
            ["http", False],
            ["HTTP", False],
            ["api://123", True],
            [" ", True],
        ],
    )
    def test_is_from_streaming_connection(self, service_url, expected):
        activity = Activity(type="message", service_url=service_url)
        assert activity.is_from_streaming_connection() == expected

    def test_serialize_basic(self, activity):
        activity_copy = Activity(
            **activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        )
        assert activity_copy == activity

    def test_get_mentions(self):
        activity = Activity(
            type="message",
            entities=[
                Mention(text="Hello"),
                Entity(type="other"),
                Entity(type="mention", text="Another mention"),
            ],
        )
        mentions = activity.get_mentions()
        assert mentions == [
            Mention(text="Hello"),
            Entity(type="mention", text="Another mention"),
        ]
