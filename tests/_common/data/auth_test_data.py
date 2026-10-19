from microsoft_agents.hosting.core import AuthHandlerSettings


def create_test_auth_handler(
    name: str, obo: bool = False, title: str = None, text: str = None
) -> AuthHandlerSettings:
    """
    Creates a test AuthHandlerSettings instance with standardized connection names.

    This helper function simplifies the creation of AuthHandlerSettings objects for testing
    by automatically generating connection names based on the provided name and
    optionally including On-Behalf-Of (OBO) connection configuration.

    Args:
        name: Base name for the auth handler, used to generate connection names
        obo: Whether to include On-Behalf-Of connection configuration
        title: Optional title for the auth handler
        text: Optional descriptive text for the auth handler

    Returns:
        AuthHandlerSettings: Configured auth handler instance with test-friendly connection names
    """
    return AuthHandlerSettings(
        name,
        abs_oauth_connection_name=f"{name}-abs-connection",
        obo_connection_name=f"{name}-obo-connection" if obo else None,
        title=title,
        text=text,
    )


class AUTH_TEST_DATA:
    def __init__(self):

        self.auth_handler: AuthHandlerSettings = create_test_auth_handler("graph")

        self.auth_handlers: dict[str, AuthHandlerSettings] = {
            "graph": create_test_auth_handler("graph"),
            "github": create_test_auth_handler("github", obo=True),
            "slack": create_test_auth_handler("slack", obo=True),
        }
