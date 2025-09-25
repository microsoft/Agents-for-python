from microsoft_agents.activity import load_configuration_from_env

from .test_defaults import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

_TEST_AGENTIC_ENV_RAW = """
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME={abs_oauth_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__OBOCONNECTIONNAME={obo_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TITLE={auth_handler_title}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TEXT={auth_handler_text}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TYPE=UserAuthorization
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{agentic_auth_handler_id}__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME={agentic_abs_oauth_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{agentic_auth_handler_id}__SETTINGS__OBOCONNECTIONNAME={agentic_obo_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{agentic_auth_handler_id}__SETTINGS__TITLE={agentic_auth_handler_title}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{agentic_auth_handler_id}__SETTINGS__TEXT={agentic_auth_handler_text}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{agentic_auth_handler_id}__SETTINGS__TYPE=AgenticAuthorization
""".format(
    abs_oauth_connection_name=DEFAULTS.abs_oauth_connection_name,
    obo_connection_name=DEFAULTS.obo_connection_name,
    auth_handler_id=DEFAULTS.auth_handler_id,
    auth_handler_title=DEFAULTS.auth_handler_title,
    auth_handler_text=DEFAULTS.auth_handler_text,
    agentic_abs_oauth_connection_name=DEFAULTS.agentic_abs_oauth_connection_name,
    agentic_obo_connection_name=DEFAULTS.agentic_obo_connection_name,
    agentic_auth_handler_id=DEFAULTS.agentic_auth_handler_id,
    agentic_auth_handler_title=DEFAULTS.agentic_auth_handler_title,
    agentic_auth_handler_text=DEFAULTS.agentic_auth_handler_text,
)


def TEST_AGENTIC_ENV():
    lines = _TEST_AGENTIC_ENV_RAW.strip().split("\n")
    env = {}
    for line in lines:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def TEST_AGENTIC_ENV_DICT():
    return load_configuration_from_env(TEST_AGENTIC_ENV())
