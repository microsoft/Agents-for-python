import os

from dotenv import load_dotenv

from microsoft_agents.activity import (
    load_configuration_from_env,
)
from microsoft_agents.hosting.core import (
    Authorization,
    MemoryStorage,
)
from microsoft_agents.authentication.msal import MsalConnectionManager

load_dotenv()

CONFIG = load_configuration_from_env(os.environ)

STORAGE = MemoryStorage()
CONNECTIONS = MsalConnectionManager(**CONFIG)
ADAPTER = A2AAdapter()
AUTHORIZATION = Authorization(STORAGE, CONNECTIONS, **CONFIG)

