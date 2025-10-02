# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import re
from dotenv import load_dotenv

from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import (
    Authorization,
    MemoryStorage,
    AgentApplication,
    TurnState,
    MemoryStorage,
    RouteRank,
    TurnContext,
)
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager

# Load configuration from environment
load_dotenv()
agents_sdk_config = load_configuration_from_env(os.environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)
APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)


@APP.activity("message", rank=RouteRank.LAST)
async def on_message(context: TurnContext, state: TurnState):
    await context.send_activity(f"Echo: {context.activity.text}")
