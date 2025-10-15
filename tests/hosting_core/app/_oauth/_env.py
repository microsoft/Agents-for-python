from tests._common.data import DEFAULT_TEST_VALUES

DEFAULTS = DEFAULT_TEST_VALUES()


def ENV_CONFIG():
    return {
        "AGENTAPPLICATION": {
            "USERAUTHORIZATION": {
                "HANDLERS": {
                    DEFAULTS.connection_name: {
                        "SETTINGS": {AZUREBOTOAUTHCONNECTIONNAME}
                    }
                }
            }
        }
    }
