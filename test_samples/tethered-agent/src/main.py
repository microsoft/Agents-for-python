import tethered

tethered.activate(allow=[
    "login.microsoftonline.com",
    "login.botframework.*",
    "api.botframework.*",
    "www.botframework.",
])

from .agent import AGENT_APP, ADAPTER, agents_sdk_config
from .start_server import start_server

start_server(
    agent_application=AGENT_APP,
    adapter=ADAPTER,
    config=agents_sdk_config,
)
