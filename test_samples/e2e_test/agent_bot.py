import re
import sys
import traceback
from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv
 
from os import environ, path
from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft.agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
    MessageFactory
)
from microsoft.agents.authentication.msal import MsalConnectionManager
from microsoft.agents.activity import (
    load_configuration_from_env,
    ActivityTypes,
    InvokeResponse,
    Activity,
    ConversationUpdateTypes
)
 
from openai import AsyncAzureOpenAI
 
 
load_dotenv(path.join(path.dirname(__file__), ".env"))
 
agents_sdk_config = load_configuration_from_env(environ)
 
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)
 
client = AsyncAzureOpenAI(
    api_version=environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
)
 
AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)
 
multiple_message_pattern = re.compile(r"(\w+)\s+(\d+)")
weather_message_pattern = re.compile(r"What's the weather in (\w+) today\?")
weather_multi_message_loop_pattern = re.compile(r"^w: .*")
 
 
@AGENT_APP.conversation_update(ConversationUpdateTypes.MEMBERS_ADDED)
async def on_members_added(context: TurnContext, _state: TurnState):
   
    await context.send_activity(MessageFactory.text("Hello and Welcome!"))
    # return True
 
 
@AGENT_APP.message(multiple_message_pattern)
async def on_multiple_message(context: TurnContext, state: TurnState):
    counter = state.get_value("ConversationState.counter", default_value_factory=(lambda: 0), target_cls=int)
 
    match = multiple_message_pattern.match(context.activity.text)
    if not match:
        return
    word = match.group(1)
    count = int(match.group(2))
    for _ in range(count):
        await context.send_activity(f"[{counter}] You said: {word}")
        counter += 1
 
    state.set_value("ConversationState.counter", counter)
 
 
@AGENT_APP.message(re.compile(r"^poem$"))
async def on_poem_message(context: TurnContext, state: TurnState):
 
    try:
        context.streaming_response.queue_informative_update(
                "Hold on for an awesome poem about Apollo..."
            )
 
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """
                        You are a creative assistant who has deeply studied Greek and Roman Gods, You also know all of the Percy Jackson Series
                        You write poems about the Greek Gods as they are depicted in the Percy Jackson books.
                        You format the poems in a way that is easy to read and understand
                        You break your poems into stanzas
                        You format your poems in Markdown using double lines to separate stanzas
                    """
                },
                {
                    "role": "user",
                    "content": "Write a poem about the Greek God Apollo as depicted in the Percy Jackson books"
                }
            ],
            stream=True,
            max_tokens=1000
        )
       
        async for update in stream:
            if len(update.choices) > 0:
                delta = update.choices[0].delta
                if delta.content:
                    context.streaming_response.queue_text_chunk(delta.content)
    finally:
        await context.streaming_response.end_stream()
 
 
@AGENT_APP.activity(ActivityTypes.message)
async def on_message(context: TurnContext, state: TurnState):
    counter = state.get_value("ConversationState.counter", default_value_factory=(lambda: 0), target_cls=int)
    await context.send_activity(f"[{counter}] You said: {context.activity.text}")
    counter += 1
    state.set_value("ConversationState.counter", counter)
 
 
@AGENT_APP.activity(ActivityTypes.invoke)
async def on_invoke(context: TurnContext, state: TurnState):
    invoke_response = InvokeResponse(
        status=200, body={"message": "Invoke received.", "data": context.activity.value}
    )
   
    await context.send_activity(
        Activity(type=ActivityTypes.invoke_response, value=invoke_response)
    )
 
# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    agent: AgentApplication = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )
 
 
APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = CONNECTION_MANAGER.get_default_connection_configuration()
APP["agent_app"] = AGENT_APP
APP["adapter"] = ADAPTER
 
if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error