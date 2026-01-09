import pytest

from microsoft_agents.activity import Activity

from microsoft_agents.testing import (
    Integration,
    AiohttpEnvironment
)

from ..samples import QuickstartSample


class TestExpectReplies(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment

    @pytest.mark.asyncio
    async def test_expect_replies_without_service_url(
        self, agent_client, response_client
    ):

        activity = Activity(
            type="message",
            text="hi",
            conversation={"id": "conv-id"},
            channel_id="test",
            from_property={"id": "from-id"},
            recipient={"id": "to-id"},
            delivery_mode="expectReplies",
            locale="en-US",
        )

        res = await agent_client.send_expect_replies(activity)

        assert len(res) > 0
        assert isinstance(res[0], Activity)
