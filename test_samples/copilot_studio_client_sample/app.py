import asyncio
from dotenv import load_dotenv
from os import environ, path
from msal import PublicClientApplication

from microsoft_agents.copilotstudio.client import ConnectionSettings, CopilotClient

from msal_cache_plugin import get_msal_token_cache
from chat_console_service import ChatConsoleService
from config import McsConnectionSettings

load_dotenv(path.join(path.dirname(__file__), ".env"))
mcs_connection_settings = McsConnectionSettings()


def acquire_token(mcs_settings: McsConnectionSettings, cache_path: str) -> str:
    cache = get_msal_token_cache(cache_path)
    app = PublicClientApplication(
        mcs_settings.app_client_id,
        authority=f"https://login.microsoftonline.com/{mcs_settings.tenant_id}",
        token_cache=cache,
    )

    token_scopes = ["https://api.powerplatform.com/.default"]

    accounts = app.get_accounts()

    if accounts:
        # If so, you could then somehow display these accounts and let end user choose
        chosen = accounts[0]
        result = app.acquire_token_silent(scopes=token_scopes, account=chosen)
    else:
        # At this point, you can save you can update your cache if you are using token caching
        # check result variable, if its None then you should interactively acquire a token
        # So no suitable token exists in cache. Let's get a new one from Microsoft Entra.
        result = app.acquire_token_interactive(scopes=token_scopes)

    if "access_token" in result:
        return result["access_token"]
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        raise Exception("Authentication with the Public AgentApplication failed")


def create_mcs_client(connection_settings: ConnectionSettings) -> CopilotClient:
    token = acquire_token(
        connection_settings,
        environ.get("TOKEN_CACHE_PATH")
        or path.join(path.dirname(__file__), "bin/token_cache.bin"),
    )
    return CopilotClient(connection_settings, token)


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(
        ChatConsoleService(create_mcs_client(mcs_connection_settings)).start_service()
    )
finally:
    loop.close()
