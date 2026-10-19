from agent import AGENT_APP, CONNECTION_MANAGER, ADAPTER
from start_server import start_server

if __name__ == "__main__":
    try:
        start_server(
            agent_application=AGENT_APP,
            adapter=ADAPTER,
            auth_configuration=CONNECTION_MANAGER.get_default_connection_configuration(),
        )
    except Exception as error:
        raise error
