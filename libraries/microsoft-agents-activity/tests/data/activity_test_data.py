from microsoft_agents.activity import (
    Activity,
    Attachment
)

def GEN_TEST_CHANNEL_DATA():
    return [ None, {}, MyChannelData() ]

def GEN_HAS_CONTENT_DATA():
    return [
        (Activity(text="text"), True),
        (Activity(summary="summary"), True),
        (Activity(attachments=[Attachment()]), True),
        (Activity(channel_data=MyChannelData()), True),
        (Activity(), False)
    ]

class MyChannelData:
    foo: str
    bar: str

class TestActivity(Activity):
    def is_target_activity_type(activity_type: str) -> bool:
        return self.is_activity(activity_type)