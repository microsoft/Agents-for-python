"""
If you are looking for more mocking capabilities for the SDK's core components,
consider taking a look at the /tests/_common directory under the Python SDK's root.
"""

from typing import Protocol

from microsoft_agents.hosting.core import (
    ChannelAdapter
)

class MockSimpleAdapter(ChannelAdapter):

    def __init__(self, app: AgentApplication, client: MockClient):
        super().__init__()
        self._app = None
        self._client = None

    def run(self, app: AgentApplication, client: MockClient):
        self._app = app
        self._client = client
        # Simulate receiving an activity
        activity = Activity(
            type="message",
            id="1234",
            timestamp=datetime.utcnow(),
            service_url="https://service.url/",
            channel_id="mock_channel",
            from_property=ChannelAccount(id="user1", name="User One"),
            recipient=ChannelAccount(id="bot", name="Bot"),
            conversation=ConversationAccount(id="conv1"),
            text="Hello, Bot!"
        )
        self._client.on_activity(activity, self)

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