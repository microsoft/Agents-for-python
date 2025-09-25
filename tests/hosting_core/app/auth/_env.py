from tests._common.data import TEST_DEFAULTS

DEFAULTS = TEST_DEFAULTS()

def ENV_CONFIG():
    return {
        "AGENTAPPLICATION": {
            "USERAUTHORIZATION": {
                "HANDLERS": {
                    DEFAULTS.connection_name: {
                        "SETTINGS": {
                            AZUREBOTOAUTHCONNECTIONNAME
                        }
                    }
                }
            }
        }
    }