import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Entity,
    EntityTypes,
    Mention,
    ResourceResponse,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    DeliveryModes
)

def helper_create_activity(locale: str, create_recipient: bool = True, create_from: bool = True) -> Activity:
    properties = {
        "name": "Value"
    }
    account1 = None
    if create_from:
        account1 = ChannelAccount(
            id="ChannelAccount_Id_1",
            name="ChannelAccount_Name_1",
            properties=properties,
            role="ChannelAccount_Role_1",
        )
    
    account2 = None
    if create_recipient:
        account2 = ChannelAccount(
            id="ChannelAccount_Id_2",
            name="ChannelAccount_Name_2",
            properties=properties,
            role="ChannelAccount_Role_2",
        )
    
    conversation_account = ConversationAccount(
        conversation_type = "a",
        id = "123",
        is_group = True,
        name = "Name",
        properties = properties,
        role = "ConversationAccount_Role",
    )

    activity = Activity(
        id="123",
        from_property = account1,
        recipient = account2,
        conversation = conversation_account,
        channel_id = "ChannelId123",
        locale = locale,
        service_url = "ServiceUrl123",
        type="message"
    )
    return activity

def helper_get_activity_type(type: str) -> str:
    return None # robrandao : TODO -> why

def helper_validate_recipient_and_from(activity: Activity, create_recipient: bool, create_from: bool):
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
        return helper_create_activity("en-us")

    def conversation_assert_helper(self, activity, conversation_reference):
        assert activity.id == conversation_reference.activity_id
        assert activity.from_property.id == conversation_reference.user.id
        assert activity.recipient.id == conversation_reference.agent.id
        assert activity.conversation.id == conversation_reference.conversation.id
        assert activity.channel_id == conversation_reference.channel_id
        assert activity.locale == conversation_reference.locale
        assert activity.service_url == conversation_reference.service_url

    def test_get_conversation_reference(self, activity):
        conversation_reference = activity.get_conversation_reference()
        self.conversation_assert_helper(activity, conversation_reference)

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
            text=None
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
            text="<at>firstName</at>"
        )
        lst = []

        output = mention.model_dump()
        entity = Entity(**output)

        lst.append(entity)
        activity.entities = lst

        stripped_activity_text = activity.remove_recipient_mention()
        assert stripped_activity_text == expected_stripped_name

    def test_apply_conversation_reference_is_incoming(self):
        activity = helper_create_activity("en-uS") # on purpose
        conversation_reference = ConversationReference(
            channel_id = "cr_123",
            service_url = "cr_serviceUrl",
            conversation = ConversationAccount(id="cr_456"),
            user = ChannelAccount(id="cr_abc"),
            agent = ChannelAccount(id="cr_def"),
            activity_id = "cr_12345",
            locale = "en-us",
            delivery_mode = DeliveryModes.expect_replies
        )

        activity_to_send = activity.apply_conversation_reference(conversation_reference, is_incoming=True)
        conversation_reference = activity_to_send.get_conversation_reference()

        self.conversation_assert_helper(activity, conversation_reference)
        assert activity.locale == activity_to_send.locale

    @pytest.mark.parametrize("locale", ["EN-US", "en-uS"])
    def test_apply_conversation_reference(self, locale):
        activity = helper_create_activity(locale)
        conversation_reference = ConversationReference(
            channel_id = "123",
            service_url = "serviceUrl",
            conversation = ConversationAccount(id="456"),
            user = ChannelAccount(id="abc"),
            agent = ChannelAccount(id="def"),
            activity_id = "12345",
            locale = "en-us",
        )

        activity_to_send = activity.apply_conversation_reference(conversation_reference, is_incoming=False)

        self.conversation_assert_helper(activity, conversation_reference)

        if locale is None:
            assert conversation_reference.locale == activity_to_send.locale
        else:
            assert activity.locale == activity_to_send.locale

    @pytest.mark.parametrize("value, value_type, create_recipient, create_from, label", [
        ["myValue", None, False, False, None],
        [None, None, False, False, None],
        [None, "myValueType", False, False, None],
        [None, None, True, False, None],
        [None, None, False, True, "testLabel"]
    ])
    def test_create_trace(self, value, value_type, create_recipient, create_from, label):
        activity = helper_create_activity("en-us", create_recipient, create_from)
        trace_activity = activity.create_trace("test", value, value_type, label)

        assert trace is not None
        assert trace.type == ActivityTypes.trace
        if value_type:
            assert trace.value_type == value.get_type.name
        elif value:
            assert trace.value_type == value.get_type.name
        else:
            assert trace.value_type is None
        assert trace.label == label
        assert trace.name == "test"

    @pytest.mark.parametrize(
        "activity_type",
        [
            ActivityTypes.end_of_conversation,
            ActivityTypes.event,
            ActivityTypes.handoff,
            ActivityTypes.invoke,
            ActivityTypes.message,
            ActivityTypes.message,
            ActivityTypes.typing
        ]
    )
    def test_can_create_activities(self, activity_type):
        pass
        # create_activity_method = Activity.create_activity_method_map.get(activity_type)
        # activity = create_activity_method.invoke(None, {})
        # expected_activity_type = 


        # # huh?

    @pytest.mark.parametrize(
        "name, value_type, value, label",
        [
            ["TestTrace", None, None, None],
            ["TestTrace", None, "TestValue", None]
        ]
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
            [None, None, True, True, None]
        ]
    )
    def test_can_create_reply_activity(self, activity_locale, text, create_recipient, create_from, create_reply_locale):
        activity = helper_create_activity(activity_locale, create_recipient, create_from)
        reply = activity.create_reply(text, locale=create_reply_locale)

        assert reply is not None
        assert reply.type == ActivityTypes.message
        assert reply.reply_to_id == "123"
        assert reply.service_url == "ServiceUrl123"
        assert reply.channel_id == "ChannelId123"
        assert reply.text == text or ""
        assert reply.locale == activity_locale or create_reply_locale
        validate_recipient_and_from(reply, create_recipient, create_from) # robrandao: TODO

    @pytest.mark.parametrize(
        "activity_type",
        [
            ActivityTypes.command,
            ActivityTypes.command_result,
            ActivityTypes.contact_relation_update,
            ActivityTypes.conversation_update,
            ActivityTypes.end_of_conversation,
            ActivityTypes.event,
            ActivityTypes.handoff,
            ActivityTypes.installation_update,
            ActivityTypes.invoke,
            ActivityTypes.message,
            ActivityTypes.message_delete,
            ActivityTypes.message_reaction,
            ActivityTypes.message_update,
            ActivityTypes.suggestion,
            ActivityTypes.typing
        ]
    )
    def test_can_cast_to_activity_type(self, activity_type):
        activity = Activity(type=activity_type)
        activity = Activity(type=get_activity_type(activity_type))
        cast_activity = cast_to_activity_type(activity_type, activity)
        assert activity is not None
        assert cast_activity is not None
        assert activity.type.lower() == activity_type.lower()
    
    @pytest.mark.parametrize(
        "activity_type",
        [
            ActivityTypes.command,
            ActivityTypes.command_result,
            ActivityTypes.contact_relation_update,
            ActivityTypes.conversation_update,
            ActivityTypes.end_of_conversation,
            ActivityTypes.event,
            ActivityTypes.handoff,
            ActivityTypes.installation_update,
            ActivityTypes.invoke,
            ActivityTypes.message,
            ActivityTypes.message_delete,
            ActivityTypes.message_reaction,
            ActivityTypes.message_update,
            ActivityTypes.suggestion,
            ActivityTypes.typing
        ]
    )
    def test_cast_to_activity_type_returns_none_when_cast_fails(self, activity_type):
        activity = Activity(type="message")
        result = cast_to_activity_type(activity_type, activity)
        assert activity is not None
        assert activity.type is None
        assert result is None

    def get_channel_data(self, channel_data):
        activity = Activity(channel_data = channel_data)
        try:
            result = activity.get_chanel_data()
            if channel_data is None:
                assert result is None
            else:
                assert result == channel_data
        except:
            pass # robrandao: TODO

    @pytest.mark.parametrize(
        "type_of_activity, target_type, expected",
        [
            ["message/testType", ActivityTypes.message, True],
            ["message-testType", ActivityTypes.message, False],
        ]
    )
    def test_is_activity(self, type_of_activity, target_type, expected):
        activity = test_activity(type=type_of_activity)
        assert expected == activity.is_target_activity_type(target_type)
    
    def test_try_get_channel_data(self, channel_data):
        activity = Activity(channel_data=channel_data)
        success, data = activity.try_get_channel_data() # robrandao: TODO
        expected_success = get_expected_try_get_channel_data_result(channel_data)

        assert expected_success == success
        if success:
            assert data is not None
            assert isinstance(data, MyChannelData)
        else:
            assert data is None

    def test_can_set_caller_id(self):
        expected_caller_id = "caller_id"
        activity = Activity(caller_id=expected_caller_id)
        assert expected_caller_id == activity.caller_id

    def test_can_set_properties(self):
        activity = Activity(properties={})
        props = activity.properties
        assert props is not None
        assert isinstance(props, dict)

    def test_serialize_tuple_value(self):
        activity = Activity(value=("string1", "string2"))
        in_activity = Activity.validate_model(activity.model_dump())
        out_tuple_value = activity.value
        in_tuple_value = json.dump(activity.value)
        assert out_tuple_value == in_tuple_value

# class TestActivityGetEntities:

#     @pytest.fixture
#     def activity(self):
#         return Activity(
#             type="message",
#             entities=[
#                 ActivityTreatment(treatment=ActivityTreatmentType.TARGETED),
#                 Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=ActivityTreatmentType.TARGETED),
#                 Mention(type=EntityTypes.MENTION, text="Hello"),
#                 ActivityTreatment(type=""),
#                 Entity(type=EntityTypes.MENTION),
#                 Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=None),
#             ],
#         )
    
#     def test_activity_get_mentions(self, activity):
#         expected = [
#             Mention(type=EntityTypes.MENTION, text="Hello"),
#             Entity(type=EntityTypes.MENTION),
#         ]
#         ret = activity.get_mentions()
#         assert activity.get_mentions() == expected
#         assert ret[0].text == "Hello"
#         assert ret[0].type == EntityTypes.MENTION
#         assert ret[1].text is None
#         assert ret[1].type == EntityTypes.MENTION

#     def test_activity_get_activity_treatments(self, activity):
#         expected = [
#             ActivityTreatment(treatment=ActivityTreatmentType.TARGETED),
#             Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=ActivityTreatmentType.TARGETED),
#             Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=None),
#         ]
#         ret = activity.get_activity_treatments()
#         assert ret == expected
#         assert ret[0].treatment == ActivityTreatmentType.TARGETED
#         assert ret[0].type == EntityTypes.ACTIVITY_TREATMENT
#         assert ret[1].treatment == ActivityTreatmentType.TARGETED
#         assert ret[1].type == EntityTypes.ACTIVITY_TREATMENT
#         assert ret[2].treatment is None
#         assert ret[2].type == EntityTypes.ACTIVITY_TREATMENT