from microsoft_agents.hosting.core import AuthHandler


def create_test_auth_handler(
    name: str, obo: bool = False, title: str = None, text: str = None
) -> AuthHandler:
    """
    Creates a test AuthHandler instance with standardized connection names.

    This helper function simplifies the creation of AuthHandler objects for testing
    by automatically generating connection names based on the provided name and
    optionally including On-Behalf-Of (OBO) connection configuration.

    Args:
        name: Base name for the auth handler, used to generate connection names
        obo: Whether to include On-Behalf-Of connection configuration
        title: Optional title for the auth handler
        text: Optional descriptive text for the auth handler

    Returns:
        AuthHandler: Configured auth handler instance with test-friendly connection names
    """
    return AuthHandler(
        name,
        abs_oauth_connection_name=f"{name}-abs-connection",
        obo_connection_name=f"{name}-obo-connection" if obo else None,
        title=title,
        text=text,
    )


class TEST_AUTH_DATA:
    def __init__(self):

        self.auth_handler: AuthHandler = create_test_auth_handler("graph")

        self.auth_handlers: dict[str, AuthHandler] = {
            "graph": create_test_auth_handler("graph"),
            "github": create_test_auth_handler("github", obo=True),
            "slack": create_test_auth_handler("slack", obo=True),
        }
