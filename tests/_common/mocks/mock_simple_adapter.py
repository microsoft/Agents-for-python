from microsoft_agents.activity import (
    Activity
    ActivityTypes,
    ResourceResponse
)

from microsoft_agents.hosting.core import (
    ChannelAdapter
)

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