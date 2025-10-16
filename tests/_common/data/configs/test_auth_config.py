from microsoft_agents.activity import load_configuration_from_env

from ...create_env_var_dict import create_env_var_dict
from ..default_test_values import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()

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


def NON_AGENTIC_TEST_ENV():
    return create_env_var_dict(_TEST_ENV_RAW)


def NON_AGENTIC_TEST_ENV_DICT():
    return load_configuration_from_env(NON_AGENTIC_TEST_ENV())
