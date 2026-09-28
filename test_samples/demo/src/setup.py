# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from os import environ

from dotenv import load_dotenv

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.fastapi import CloudAdapter
from microsoft_agents.hosting.core import Authorization, MemoryStorage
from microsoft_agents.hosting.core.storage import ConsoleTranscriptLogger, TranscriptLoggerMiddleware

logger = logging.getLogger(__name__)
load_dotenv()

agents_sdk_config = load_configuration_from_env(environ)

storage = MemoryStorage()
connections = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connections)
adapter.use(TranscriptLoggerMiddleware(ConsoleTranscriptLogger()))
authorization = Authorization(storage, connections, **agents_sdk_config)