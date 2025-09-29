from microsoft_agents.activity import load_configuration_from_env

from tests._common import create_env_var_dict
from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

ENV_DICT = {
    "CONNECTIONS": {
        "SERVICE_CONNECTION": {
            "SETTINGS": {
                "TENANTID": DEFAULTS.connections_default_tenant_id,
                "CLIENTID": DEFAULTS.connections_default_client_id,
                "CLIENTSECRET": DEFAULTS.connections_default_client_secret,
            }
        },
        "AGENTIC": {
            "SETTINGS": {
                "TENANTID": DEFAULTS.connections_agentic_tenant_id,
                "CLIENTID": DEFAULTS.connections_agentic_client_id,
                "CLIENTSECRET": DEFAULTS.connections_agentic_client_secret,
            }
        }
    },
    "AGENTAPPLICATION": {
        "USERAUTHORIZATION": {
            "HANDLERS": {
                DEFAULTS.auth_handler_id: {
                    "SETTINGS": {
                        "AZUREBOTOAUTHCONNECTIONNAME": DEFAULTS.abs_oauth_connection_name,
                        "OBOCONNECTIONNAME": DEFAULTS.obo_connection_name,
                        "TITLE": DEFAULTS.auth_handler_title,
                        "TEXT": DEFAULTS.auth_handler_text,
                        "TYPE": "UserAuthorization",
                    }
                },
                DEFAULTS.agentic_auth_handler_id: {
                    "SETTINGS": {
                        "AZUREBOTOAUTHCONNECTIONNAME": DEFAULTS.agentic_abs_oauth_connection_name,
                        "OBOCONNECTIONNAME": DEFAULTS.agentic_obo_connection_name,
                        "TITLE": DEFAULTS.agentic_auth_handler_title,
                        "TEXT": DEFAULTS.agentic_auth_handler_text,
                        "TYPE": "AgenticAuthorization",
                    }
                },
            }
        },
    },
    "CONNECTIONSMAP": [
        {
            "CONNECTION": "SERVICE_CONNECTION",
            "SERVICEURL": "*"
        },
        {
            "CONNECTION": "AGENTIC",
            "SERVICEURL": "agentic"
        }
    ]
}

ENV_RAW = """
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID={connections_default_tenant_id}
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID={connections_default_client_id}
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET={connections_default_client_secret}

CONNECTIONS__AGENTIC__SETTINGS__TENANTID={connections_agentic_tenant_id}
CONNECTIONS__AGENTIC__SETTINGS__CLIENTID={connections_agentic_client_id}
CONNECTIONS__AGENTIC__SETTINGS__CLIENTSECRET={connections_agentic_client_secret}

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

CONNECTIONSMAP__0__CONNECTION=SERVICE_CONNECTION
CONNECTIONSMAP__0__SERVICEURL=*
CONNECTIONSMAP__1__CONNECTION=AGENTIC
CONNECTIONSMAP__1__SERVICEURL=agentic
""".format(
    connections_default_tenant_id=DEFAULTS.connections_default_tenant_id,
    connections_default_client_id=DEFAULTS.connections_default_client_id,
    connections_default_client_secret=DEFAULTS.connections_default_client_secret,
    connections_agentic_tenant_id=DEFAULTS.connections_agentic_tenant_id,
    connections_agentic_client_id=DEFAULTS.connections_agentic_client_id,
    connections_agentic_client_secret=DEFAULTS.connections_agentic_client_secret,
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


def test_load_configuration_from_env():
    input_dict = create_env_var_dict(ENV_RAW)
    config = load_configuration_from_env(input_dict)
    assert config == ENV_DICT