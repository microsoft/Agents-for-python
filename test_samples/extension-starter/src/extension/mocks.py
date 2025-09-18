"""
If you are looking for more mocking capabilities for the SDK's core components,
consider taking a look at the /tests/_common directory under the Python SDK's root.
"""

class MockSimpleAdapter(ChannelAdapter):

    def __init__(self):
        super().__init__()

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

class MockClient:

    def __init__(self, adapter: ChannelAdapter, on_activity: Awaitable[Activity, None] = None):
        self._adapater = adapter
        self._on_activity = None

    def on_activity(self, handler: Awaitable[Activity, None]):
        self._on_activity = handler

    
    