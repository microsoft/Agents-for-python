import tethered

tethered.activate(allow=[
    "login.microsoftonline.com",
    "login.botframework.*",
    "api.botframework.*",
    "www.botframework.",
])

from .agent import AGENT_APP, CONNECTION_MANAGER
from .start_server import start_server

start_server(
    agent_application=AGENT_APP,
    auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
)
