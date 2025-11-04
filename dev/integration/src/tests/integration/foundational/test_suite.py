import json
import pytest
import asyncio

from microsoft_agents.activity import (
    ActivityTypes,
)

from src.core import integration, IntegrationFixtures, AiohttpEnvironment
from src.samples import QuickstartSample

from ._common import load_activity

DIRECTLINE = "directline"

@integration()
class TestFoundation(IntegrationFixtures):

    def load_activity(self, activity_name) -> Activity:
        return load_activity(DIRECTLINE, activity_name)

    @pytest.mark.asyncio
    async def test__send_activity__sends_hello_world__returns_hello_world(self, agent_client):
        activity = load_activity(DIRECTLINE, "hello_world.json")
        result = await agent_client.send_activity(activity)
        assert result is not None
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert last.text.lower() == "you said: {activity.text}".lower()

    @pytest.mark.asyncio
    async def test__send_invoke__send_basic_invoke_activity__receive_invoke_response(self, agent_client):
        activity = load_activity(DIRECTLINE, "basic_invoke.json")
        result = await agent_client.send_activity(activity)
        assert result
        data = json.loads(result)
        message = data.get("message", {})
        assert "Invoke received." in message
        assert "data" in data
        assert data["parameters"] and len(data["parameters"]) > 0
        assert "hi" in data["value"]

    @pytest.mark.asyncio
    async def test__send_activity__sends_message_activity_to_ac_submit__return_valid_response(self, agent_client):
        activity = load_activity(DIRECTLINE, "ac_submit.json")
        result = await agent_client.send_activity(activity)
        assert result is not None
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert "doStuff" in last.text
        assert "Action.Submit" in last.text
        assert "hello" in last.text

    @pytest.mark.asyncio
    async def test__send_invoke_sends_invoke_activity_to_ac_execute__returns_valid_adaptive_card_invoke_response(self, agent_client):
        activity = load_activity(DIRECTLINE, "ac_execute.json")
        result = await agent_client.send_invoke(activity)

        result = json.loads(result)

        assert result.status == 200
        assert result.value

        assert "application/vnd.microsoft.card.adaptive" in result.type

        activity_data = json.loads(activity.value)
        assert activity_data.get("action")
        user_text = activity_data.get("usertext")
        assert user_text in result.value

    @pytest.mark.asyncio
    async def test__send_activity_sends_text__returns_poem(self, agent_client):
        pass

    @pytest.mark.asyncio
    async def test__send_expected_replies_activity__sends_text__returns_poem(self, agent_client):
        activity = self.load_activity("expected_replies.json")
        result = await agent_client.send_expected_replies(activity)
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert "Apollo" in last.text
        assert "\n" in last.text

    @pytest.mark.asyncio
    async def test__send_invoke__query_link__returns_text(self, agent_client):
        activity = self.load_activity("query_link.json")
        result = await agent_client.send_invoke(activity)
        pass # TODO

    @pytest.mark.asyncio
    async def test__send_invoke__select_item__receive_item(self, agent_client):
        activity = self.load_activity("select_item.json")
        result = await agent_client.send_invoke(activity)
        pass # TODO

    @pytest.mark.asyncio
    async def test__send_activity__conversation_update__returns_welcome_message(self, agent_client):
        activity = self.load_activity("conversation_update.json")
        result = await agent_client.send_activity(activity)
        last = result[-1]
        assert "Hello and Welcome!" in last.text

    @pytest.mark.asyncio
    async def test__send_activity__send_heart_message_reaction__returns_message_reaction_heart(self, agent_client):
        activity = self.load_activity("message_reaction_heart.json")
        result = await agent_client.send_activity(activity)
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert "Message Reaction Added: heart" in last.text

    @pytest.mark.asyncio
    async def test__send_activity__remove_heart_message_reaction__returns_message_reaction_heart(self, agent_client):
        activity = self.load_activity
        result = await agent_client.send_activity(activity)
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert "Message Reaction Removed: heart" in last.text

    @pytest.mark.asyncio
    async def test__send_expected_replies_activity__send_seattle_today_weather__returns_weather(self, agent_client):
        activity = self.load_activity("expected_replies_seattle_weather.json")
        result = await agent_client.send_expected_replies(activity)
        last = result[-1]
        assert last.type == ActivityTypes.message
        assert last.attachments and len(last.attachments) > 0
        
        adaptive_card = last.attachments.first()
        assert adaptive_card
        assert "application/vnd.microsoft.card.adaptive" == adaptive_card.content_type
        assert adaptive_card.content

        assert \
            "�" in adaptive_card.content or \
            "\\u00B0" in adaptive_card.content or \
            f"Missing temperature inside adaptive card: {adaptive_card.content}" in adaptive_card.content

    @pytest.mark.asyncio
    async def test__send_activity__simulate_message_loop__expect_question_about_time_and_returns_weather(self, agent_client):
        activities = self.load_activity("message_loop_1.json")
        fresult = await agent_client.send_activity(activities[0])
        assert 