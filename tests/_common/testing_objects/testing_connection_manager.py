class TestingConnectionManager(Connections):
    """
    Connection manager for unit tests.

    This test double provides a simplified connection management interface that
    returns TestingTokenProvider instances for all connection requests. It enables
    testing of authorization flows without requiring actual OAuth configurations
    or external authentication services.
    """

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        """
        Get a token provider for the specified connection name.

        Args:
            connection_name: Name of the OAuth connection

        Returns:
            AccessTokenProviderBase: TestingTokenProvider configured with the connection name
        """
        return TestingTokenProvider(connection_name)

    def get_default_connection(self) -> AccessTokenProviderBase:
        """
        Get the default token provider.

        Returns:
            AccessTokenProviderBase: TestingTokenProvider configured with "default" name
        """
        return TestingTokenProvider("default")

    def get_token_provider(
        self, claims_identity: ClaimsIdentity, service_url: str
    ) -> AccessTokenProviderBase:
        """
        Get a token provider based on claims identity and service URL.

        In this test implementation, returns the default connection regardless
        of the provided parameters.

        Args: (unused in test implementation)
            claims_identity: User's claims and identity information
            service_url: URL of the service requiring authentication

        Returns:
            AccessTokenProviderBase: The default TestingTokenProvider
        """
        return self.get_default_connection()

    def get_default_connection_configuration(self) -> AgentAuthConfiguration:
        """
        Get the default authentication configuration.

        Returns:
            AgentAuthConfiguration: Empty configuration suitable for testing
        """
        return AgentAuthConfiguration()