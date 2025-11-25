import pytest
import logging

from microsoft_agents.activity import Activity

from microsoft_agents.testing import (
    ddt,
    Integration,
    AiohttpEnvironment,
)

from ..samples import BasicSample

class BasicSampleWithLogging(BasicSample):

    async def init_app(self):

        logging.getLogger("microsoft_agents").setLevel(logging.DEBUG)

        await super().init_app()


class TestBasicDirectline(Integration):
    _sample_cls = BasicSampleWithLogging
    _environment_cls = AiohttpEnvironment

    @pytest.mark.asyncio
    async def test_expect_replies_without_service_url(self, agent_client, response_client):

        activity = Activity(
            type="message",
            text="hi",
            conversation={"id":"conv-id"},
            channel_id="test",
            from_property={"id":"from-id"},
            to={"id":"to-id"},
            delivery_mode="expectReplies",
            locale="en-US",
        )

        res = await agent_client.send_expect_replies(activity)
        
        breakpoint()
        res = Activity.model_validate(res)