import re
from os import environ
from typing import Union
from dotenv import load_dotenv

from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field

from microsoft.agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MessageFactory,
    MemoryStorage,
)
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.authentication.msal import MsalConnectionManager

from microsoft.agents.activity import Attachment, load_configuration_from_env

from agents import (
    Agent as OpenAIAgent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
)

from .tools import get_weather, get_date

load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

# robrandao : todo
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
CLIENT = AsyncAzureOpenAI(
    api_version=environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=environ["AZURE_OPENAI_ENDPOINT"],
    azure_ad_token_provider=token_provider,
)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or "gpt-4o-mini", openai_client=CLIENT
        )


custom_model_provider = CustomModelProvider()

agent = OpenAIAgent(
    name="WeatherAgent",
    instructions=""""
    You are a friendly assistant that helps people find a weather forecast for a given time and place.
    Do not reply with MD format nor plain text. You can ONLY respond in JSON format with the following JSON schema
    {
        "contentType": "'Text' if you don't have a forecast or 'AdaptiveCard' if you do",
        "content": "{The content of the response, may be plain text, or JSON based adaptive card}"
    }
    You may ask follow up questions until you have enough information to answer the customers question,
    but once you have a forecast forecast, make sure to format it nicely using an adaptive card.
    """,
    tools=[get_weather, get_date],
)


class WeatherForecastAgentResponse(BaseModel):
    contentType: str = Field(pattern=r"^(Text|AdaptiveCard)$")
    content: Union[dict, str]


@AGENT_APP.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    members_added = context.activity.members_added
    for member in members_added:
        if member.id != context.activity.recipient.id:
            await context.send_activity("Hello and welcome!")


@AGENT_APP.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    response = await Runner.run(
        agent,
        context.activity.text,
        run_config=RunConfig(
            model_provider=custom_model_provider,
            tracing_disabled=True,
        ),
    )
    print(f"Response: {response.final_output}")
    json_response = response.final_output
    if "json" in json_response and json_response.index("json") < json_response.index(
        "{"
    ):
        # a common pattern with OpenAI responses is that they may contain a "json" prefix
        json_response = json_response[json_response.index("{") :]
    llm_response = WeatherForecastAgentResponse.model_validate_json(json_response)

    activity = None
    if llm_response.contentType == "AdaptiveCard":
        activity = MessageFactory.attachment(
            Attachment(
                content_type="application/vnd.microsoft.card.adaptive",
                content=llm_response.content,
            )
        )
    elif llm_response.contentType == "Text":
        activity = MessageFactory.text(llm_response.content)

    return await context.send_activity(activity)
