from microsoft_agents.activity import (
    Activity,
    Attachment,
    Mention,
    GeoCoordinates,
    Place,
    Thing,
    Entity
)

class MyChannelData:
    foo: str
    bar: str

def GEN_HAS_CONTENT_DATA():
    return [
        (Activity(text="text"), True),
        (Activity(summary="summary"), True),
        (Activity(attachments=[Attachment()]), True),
        (Activity(channel_data=MyChannelData()), True),
        (Activity(), False)
    ]

def GEN_TEST_CHANNEL_DATA():
    return [ None, {}, MyChannelData() ]