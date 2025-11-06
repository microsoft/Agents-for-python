from microsoft_agents.activity import Activity


def populate_activity(original: Activity, defaults: Activity | dict) -> Activity:

    if isinstance(defaults, Activity):
        defaults = defaults.model_dump(exclude_unset=True)

    new_activity = original.model_copy()

    for key in defaults.keys():
        if getattr(new_activity, key) is None:
            setattr(new_activity, key, defaults[key])

    return new_activity


# def _populate_incoming_activity(activity: Activity) -> Activity:

#     activity = activity.model_copy()

#     if not activity.locale:
#         activity.locale = "en-US"

#     if not activity.channel_id:
#         activity.channel_id = "emulator"

#     if not activity.delivery_mode:
#         activity.delivery_mode = DeliveryModes.normal

#     if not activity.service_url:
#         activity.service_url = "http://localhost"

#     if not activity.recipient:
#         activity.recipient = ChannelAccount(id="agent", name="Agent")

#     if not activity.from_property:
#         activity.from_property = ChannelAccount(id="user", name="User")

#     if not activity.conversation:
#         activity.conversation = ConversationAccount(id="conversation1")

#     return activity
