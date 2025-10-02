ENV_CONFIG = {
    "CONNECTIONS": {
        "SERVICE_CONNECTION": {
            "SETTINGS": {
                "TENANTID": "test-tenant-id-SERVICE_CONNECTION",
                "CLIENTID": "test-client-id-SERVICE_CONNECTION",
                "CLIENTSECRET": "test-client-secret-SERVICE_CONNECTION",
            }
        },
        "AGENTIC": {
            "SETTINGS": {
                "TENANTID": "test-tenant-id-AGENTIC",
                "CLIENTID": "test-client-id-AGENTIC",
                "CLIENTSECRET": "test-client-secret-AGENTIC",
            }
        },
        "MISC": {
            "SETTINGS": {
                "TENANTID": "test-tenant-id-MISC",
                "CLIENTID": "test-client-id-MISC",
                "CLIENTSECRET": "test-client-secret-MISC",
            }
        },
    },
    "AGENTAPPLICATION": {
        "USERAUTHORIZATION": {
            "HANDLERS": {
                "graph": {
                    "SETTINGS": {
                        "AZUREBOTOAUTHCONNECTIONNAME": "graph",
                        "OBOCONNECTIONNAME": "MISC",
                        "SCOPES": ["User.Read"],
                        "TITLE": "Sign in with Microsoft",
                        "TEXT": "Sign in with your Microsoft account",
                        "TYPE": "UserAuthorization",
                    }
                },
                "github": {
                    "SETTINGS": {
                        "AZUREBOTOAUTHCONNECTIONNAME": "github",
                        "OBOCONNECTIONNAME": "SERVICE_CONNECTION",
                        "TYPE": "UserAuthorization",
                    }
                },
                "agentic": {
                    "SETTINGS": {
                        "AZUREBOTOAUTHCONNECTIONNAME": "AGENTIC",
                        "OBOCONNECTIONNAME": "MISC",
                        "SCOPES": ["https://graph.microsoft.com/.default"],
                        "TITLE": "Sign in with Agentic",
                        "TEXT": "Sign in with your Agentic account",
                        "TYPE": "AgenticUserAuthorization",
                    }
                },
            }
        }
    },
    "CONNECTIONSMAP": [
        {
            "CONNECTION": "AGENTIC",
            "SERVICEURL": "agentic",
        },
        {"CONNECTION": "MISC", "AUDIENCE": "api://misc", "SERVICEURL": "*"},
        {
            "CONNECTION": "MISC",
            "AUDIENCE": "api://misc_other",
        },
        {
            "CONNECTION": "SERVICE_CONNECTION",
            "AUDIENCE": "api://service",
            "SERVICEURL": "https://service*",
        },
        {"CONNECTION": "MISC", "SERVICEURL": "https://microsoft.com/*"},
    ],
}
