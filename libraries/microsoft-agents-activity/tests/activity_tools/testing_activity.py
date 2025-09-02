from microsoft_agents.activity import Activity, ChannelAccount, ConversationAccount
from microsoft_agents.activity._model_utils import pick_model, SkipNone


def create_test_activity(
    locale: str, create_recipient: bool = True, create_from: bool = True
) -> Activity:
    properties = {"name": "Value"}
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
        conversation_type="a",
        id="123",
        is_group=True,
        name="Name",
        properties=properties,
        role="ConversationAccount_Role",
    )
    return pick_model(
        Activity,
        id="123",
        from_property=SkipNone(account1),
        recipient=SkipNone(account2),
        conversation=conversation_account,
        channel_id="ChannelId123",
        locale=SkipNone(locale),
        service_url="ServiceUrl123",
        type="message",
    )
