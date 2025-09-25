from microsoft_agents.activity import load_configuration_from_env

from .test_defaults import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

_TEST_ENV_RAW = """
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME={abs_oauth_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__OBOCONNECTIONNAME={obo_connection_name}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TITLE={auth_handler_title}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TEXT={auth_handler_text}
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__{auth_handler_id}__SETTINGS__TYPE=UserAuthorization
""".format(
    abs_oauth_connection_name=DEFAULTS.abs_oauth_connection_name,
    obo_connection_name=DEFAULTS.obo_connection_name,
    auth_handler_id=DEFAULTS.auth_handler_id,
    auth_handler_title=DEFAULTS.auth_handler_title,
    auth_handler_text=DEFAULTS.auth_handler_text,
)


def TEST_ENV():
    lines = _TEST_ENV_RAW.strip().split("\n")
    env = {}
    for line in lines:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def TEST_ENV_DICT():
    return load_configuration_from_env(TEST_ENV())
