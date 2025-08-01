from __future__ import annotations
import logging
from aiohttp.web import Application, Request, Response, run_app
from dotenv import load_dotenv
from os import environ, path

from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from openai import AsyncAzureOpenAI

from microsoft.agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft.agents.hosting.core import (
    Authorization,
    AgentApplication,
    TurnState,
    MemoryStorage,
)
from microsoft.agents.authentication.msal import MsalConnectionManager
from microsoft.agents.activity import load_configuration_from_env, ConversationUpdateTypes, ActivityTypes
import re

from agent_bot import AgentBot

# Load environment variables
load_dotenv(path.join(path.dirname(__file__), ".env"))

# Load configuration
agents_sdk_config = load_configuration_from_env(environ)

# Initialize storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

# Initialize Semantic Kernel
kernel = Kernel()
chat_completion = AzureChatCompletion(
    deployment_name=environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
    base_url=environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
)
kernel.add_service(chat_completion)
setup_logging()
logging.getLogger("kernel").setLevel(logging.DEBUG)

# Initialize Azure OpenAI client
client = AsyncAzureOpenAI(
    api_version=environ.get("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=environ.get("AZURE_OPENAI_API_KEY"),
)

# Initialize Agent Application
AGENT_APP_INSTANCE = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

# Create and configure the AgentBot
AGENT = AgentBot(client)
AGENT.register_handlers(AGENT_APP_INSTANCE)

# Listen for incoming requests on /api/messages
async def messages(req: Request) -> Response:
    agent: AgentApplication = req.app["agent_app"]
    adapter: CloudAdapter = req.app["adapter"]
    return await start_agent_process(
        req,
        agent,
        adapter,
    )

# Create the application
APP = Application(middlewares=[jwt_authorization_middleware])
APP.router.add_post("/api/messages", messages)
APP["agent_configuration"] = CONNECTION_MANAGER.get_default_connection_configuration()
APP["agent_app"] = AGENT_APP_INSTANCE
APP["adapter"] = ADAPTER

if __name__ == "__main__":
    try:
        run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error
