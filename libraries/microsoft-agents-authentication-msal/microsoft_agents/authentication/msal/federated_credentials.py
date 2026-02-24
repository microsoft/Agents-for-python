# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# TODO: Move this to the proper location or library

from __future__ import annotations

import logging
from typing import Optional

from msal import ConfidentialClientApplication, TokenCache

logger = logging.getLogger(__name__)


class FederatedCredentialsError(ValueError):
    """Exception raised for errors in FederatedCredentialsClient."""
    pass


class FederatedCredentials(dict):
    """Configuration for Federated Credentials authentication.

    This class represents the configuration needed to authenticate using
    federated credentials with Azure.

    Attributes:
        client_id: The Client ID (App ID) of the App Registration
        tenant_id: The Tenant ID where the App Registration resides
        federated_client_id: The Managed Identity Client ID that is linked
            to the App Registration via federated credentials
        authority_endpoint: Optional custom authority endpoint
    """

    client_id = "client_id"
    tenant_id = "tenant_id"
    federated_client_id = "federated_client_id"
    authority_endpoint = "authority_endpoint"

    def __init__(self, client_id: str, tenant_id: str, federated_client_id: str, authority_endpoint: str | None = None):
        """Initialize FederatedCredentials configuration.

        Args:
            client_id: The Client ID (App ID) of the App Registration
            tenant_id: The Tenant ID
            federated_client_id: The Managed Identity Client ID linked via federated credentials
            authority_endpoint: Optional custom authority endpoint (defaults to login.microsoftonline.com/{tenant_id})
        """
        if not client_id:
            raise FederatedCredentialsError("client_id is required")
        if not tenant_id:
            raise FederatedCredentialsError("tenant_id is required")
        if not federated_client_id:
            raise FederatedCredentialsError("federated_client_id is required")

        super(FederatedCredentials, self).__init__({
            self.client_id: client_id,
            self.tenant_id: tenant_id,
            self.federated_client_id: federated_client_id,
            self.authority_endpoint: authority_endpoint or f"https://login.microsoftonline.com/{tenant_id}",
        })


class FederatedCredentialsClient(object):
    """Client for acquiring tokens using Azure Federated Credentials.

    This client provides passwordless authentication by leveraging a User Assigned
    Managed Identity that is linked to an App Registration via Federated Credentials.

    The authentication flow (proper Federated Identity Credentials with token exchange):
    1. Request MI token from Managed Identity endpoint for FIC audience (api://AzureADTokenExchange)
    2. Use MI token as client_assertion to exchange for access token via OAuth 2.0 client credentials flow
    3. Azure validates the Managed Identity and Federated Credential linkage
    4. Access token is issued for the target resource with the App Registration's identity
    5. Token can be used to authenticate with target resources

    This approach eliminates the need for client secrets or certificates while
    maintaining strong security through Azure Managed Identity and token exchange.
    """

    _AZURE_FEDERATED_TOKEN_AUDIENCE = "api://AzureADTokenExchange"
    _TOKEN_SOURCE = "token_source"
    _TOKEN_SOURCE_IDP = "identity_provider"
    _TOKEN_SOURCE_CACHE = "cache"

    __instance, _tenant = None, "federated_credentials"

    def __init__(self, federated_credentials: FederatedCredentials, *, http_client=None, token_cache=None, http_cache=None, client_capabilities: list[str] | None = None):
        """Create a federated credentials client.

        Args:
            federated_credentials: An instance of FederatedCredentials containing
                the configuration for authentication.

            http_client: Optional. An http client object. If not provided, a default will be used.
                For example, you can use ``requests.Session()``,
                optionally with exponential backoff behavior demonstrated in this recipe::

                    import requests
                    from requests.adapters import HTTPAdapter, Retry
                    s = requests.Session()
                    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[
                        429, 500, 501, 502, 503, 504])
                    s.mount('https://', HTTPAdapter(max_retries=retries))

            token_cache: Optional. It accepts a TokenCache instance to store tokens.
                It will use an in-memory token cache by default.

            http_cache: Optional. It has the same characteristics as the token cache.

            client_capabilities: Optional. Allows configuration of one or more client capabilities,
                e.g. ["CP1"]. Client capability is meant to inform the Microsoft identity platform
                (STS) what this client is capable for, so STS can decide to turn on certain features.

        Example:
            import requests
            from microsoft_agents.authentication.msal.federated_credentials import (
                FederatedCredentials, FederatedCredentialsClient
            )

            config = FederatedCredentials(
                client_id="your-app-registration-client-id",
                tenant_id="your-tenant-id",
                federated_client_id="your-managed-identity-client-id"
            )

            client = FederatedCredentialsClient(
                config,
                http_client=requests.Session()
            )

            token = client.acquire_token_for_client(resource="https://graph.microsoft.com")
        """
        if not isinstance(federated_credentials, (FederatedCredentials, dict)):
            raise FederatedCredentialsError(f"Invalid federated_credentials: {federated_credentials}")

        if isinstance(federated_credentials, dict):
            if not all(k in federated_credentials for k in [FederatedCredentials.client_id, FederatedCredentials.tenant_id, FederatedCredentials.federated_client_id]):
                raise FederatedCredentialsError("federated_credentials dict must contain client_id, tenant_id, and federated_client_id")

        self._federated_credentials = federated_credentials
        
        # Create Managed Identity credential to get FIC tokens
        try:
            from azure.identity import ManagedIdentityCredential
            self._managed_identity = ManagedIdentityCredential(
                client_id=federated_credentials[FederatedCredentials.federated_client_id]
            )
        except ImportError:
            raise FederatedCredentialsError("azure-identity package is required for FederatedCredentialsClient")
        
        # Create MSAL ConfidentialClientApplication for token exchange
        authority: str = federated_credentials.get(
            FederatedCredentials.authority_endpoint,
            f"https://login.microsoftonline.com/{federated_credentials[FederatedCredentials.tenant_id]}"
        )
        
        self._msal_app = ConfidentialClientApplication(
            client_id=federated_credentials[FederatedCredentials.client_id],
            authority=authority,
            client_credential={
                "client_assertion": self._get_client_assertion
            },
            token_cache=token_cache,
            http_client=http_client
        )
        
        self._token_cache: TokenCache = token_cache or TokenCache()
        self._client_capabilities: list[str] | None = client_capabilities
    
    def _get_client_assertion(self) -> str:
        """Get Managed Identity token to use as client assertion for token exchange.
        
        This is the first step in Federated Identity Credentials flow:
        - Request token from MI endpoint with FIC audience (api://AzureADTokenExchange)
        - This token will be used as proof of identity in the token exchange
        
        Returns:
            JWT token from Managed Identity
        """
        try:
            logger.debug("Acquiring MI token for Federated Identity Credentials audience")
            # Get MI token for FIC audience
            token = self._managed_identity.get_token(f"{self._AZURE_FEDERATED_TOKEN_AUDIENCE}/.default")
            logger.debug("Successfully acquired MI token for token exchange")
            return token.token
        except Exception as e:
            logger.error(f"Failed to get MI token for FIC: {e}")
            raise FederatedCredentialsError(f"Failed to acquire managed identity token: {e}")

    def acquire_token_for_client(self, *, resource: str, claims_challenge: str | None = None):
        """Acquire token using federated credentials with proper token exchange.

        This implements the Federated Identity Credentials flow:
        1. Get MI token for FIC audience (api://AzureADTokenExchange)
        2. Use MI token as client_assertion in OAuth 2.0 client credentials flow
        3. Exchange for access token to target resource

        The token will be automatically cached. Subsequent calls will automatically
        search from cache first.

        Args:
            resource: The resource for which the token is acquired.
                For example: "https://graph.microsoft.com" or "https://api.botframework.com"

            claims_challenge: Optional. A string representation of a JSON object
                (which contains lists of claims being requested). The tenant admin
                may choose to revoke all tokens, and then a claims challenge will
                be returned by the target resource.

        Returns:
            A dict containing the access token and related information:
            {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "Bearer",
                "expires_in": 3599,
                "resource": "https://graph.microsoft.com",
                "token_source": "identity_provider"  # or "cache"
            }

            If an error occurs, returns:
            {
                "error": "error_code",
                "error_description": "Description of the error"
            }

        Example:
            # Acquire token for Microsoft Graph
            token = client.acquire_token_for_client(
                resource="https://graph.microsoft.com"
            )

            if "access_token" in token:
                # Use token to call Microsoft Graph API
                headers = {"Authorization": f"Bearer {token['access_token']}"}
            else:
                print(f"Error: {token['error']}")
        """
        try:
            logger.debug(f"Acquiring token for resource: {resource}")
            
            # Use MSAL to acquire token with client assertion (MI token)
            # MSAL automatically handles caching:
            # 1. Checks cache first for valid token
            # 2. If not cached or expired, calls _get_client_assertion() to get MI token
            # 3. Uses MI token as client_assertion in OAuth 2.0 token request
            # 4. Exchanges for access token to the target resource
            # 5. Caches the result for future calls
            scopes: list[str] = [f"{resource}/.default"]
            
            result = self._msal_app.acquire_token_for_client(
                scopes=scopes,
                claims_challenge=claims_challenge
            )
            
            if "access_token" in result:
                logger.debug("Successfully acquired token via Federated Identity Credentials")
                result["resource"] = resource
                # Note: MSAL handles caching internally, but doesn't expose cache hit/miss info
                # Token may come from cache or be newly acquired
            else:
                logger.error(f"Token acquisition failed: {result.get('error')}: {result.get('error_description')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error acquiring token with federated credentials: {e}")
            return {
                "error": "token_acquisition_failed",
                "error_description": str(e)
            }
