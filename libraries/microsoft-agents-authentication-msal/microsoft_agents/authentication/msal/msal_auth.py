# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging
import jwt
from typing import Optional
from urllib.parse import urlparse, ParseResult as URI
from msal import (
    ConfidentialClientApplication,
    ManagedIdentityClient,
    UserAssignedManagedIdentity,
    SystemAssignedManagedIdentity,
)
from requests import Session
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from microsoft_agents.hosting.core import (
    AuthTypes,
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)

logger = logging.getLogger(__name__)


# this is deferred because jwt.decode is expensive and we don't want to do it unless we
# have logging.DEBUG enabled
class _DeferredLogOfBlueprintId:
    def __init__(self, jwt_token: str):
        self.jwt_token = jwt_token

    def __str__(self):
        payload = jwt.decode(self.jwt_token, options={"verify_signature": False})
        agentic_blueprint_id = payload.get("xms_par_app_azp")
        return f"Agentic blueprint id: {agentic_blueprint_id}"


class MsalAuth(AccessTokenProviderBase):

    _client_credential_cache = None

    def __init__(self, msal_configuration: AgentAuthConfiguration):
        self._msal_configuration = msal_configuration
        logger.debug(
            f"Initializing MsalAuth with configuration: {self._msal_configuration}"
        )

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        logger.debug(
            f"Requesting access token for resource: {resource_url}, scopes: {scopes}"
        )
        valid_uri, instance_uri = self._uri_validator(resource_url)
        if not valid_uri:
            raise ValueError("Invalid instance URL")

        local_scopes = self._resolve_scopes_list(instance_uri, scopes)
        msal_auth_client = self._create_client_application()

        if isinstance(msal_auth_client, ManagedIdentityClient):
            logger.info("Acquiring token using Managed Identity Client.")
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                resource=resource_url
            )
        elif isinstance(msal_auth_client, ConfidentialClientApplication):
            logger.info("Acquiring token using Confidential Client Application.")
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                scopes=local_scopes
            )
        else:
            auth_result_payload = None

        res = auth_result_payload.get("access_token") if auth_result_payload else None
        if not res:
            logger.error("Failed to acquire token for resource %s", auth_result_payload)
            raise ValueError(f"Failed to acquire token. {str(auth_result_payload)}")
        return res

    async def acquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        """
        Acquire a token on behalf of a user.
        :param scopes: The scopes for which to get the token.
        :param user_assertion: The user assertion token.
        :return: The access token as a string.
        """

        msal_auth_client = self._create_client_application()
        if isinstance(msal_auth_client, ManagedIdentityClient):
            logger.error(
                "Attempted on-behalf-of flow with Managed Identity authentication."
            )
            raise NotImplementedError(
                "On-behalf-of flow is not supported with Managed Identity authentication."
            )
        elif isinstance(msal_auth_client, ConfidentialClientApplication):
            # TODO: Handling token error / acquisition failed

            token = msal_auth_client.acquire_token_on_behalf_of(
                user_assertion=user_assertion, scopes=scopes
            )

            if "access_token" not in token:
                logger.error(
                    f"Failed to acquire token on behalf of user: {user_assertion}"
                )
                raise ValueError(f"Failed to acquire token. {str(token)}")

            return token["access_token"]

        logger.error(
            f"On-behalf-of flow is not supported with the current authentication type: {msal_auth_client.__class__.__name__}"
        )
        raise NotImplementedError(
            f"On-behalf-of flow is not supported with the current authentication type: {msal_auth_client.__class__.__name__}"
        )

    def _create_client_application(
        self,
    ) -> ManagedIdentityClient | ConfidentialClientApplication:
        msal_auth_client = None

        if self._msal_configuration.AUTH_TYPE == AuthTypes.user_managed_identity:
            msal_auth_client = ManagedIdentityClient(
                UserAssignedManagedIdentity(
                    client_id=self._msal_configuration.CLIENT_ID
                ),
                http_client=Session(),
            )

        elif self._msal_configuration.AUTH_TYPE == AuthTypes.system_managed_identity:
            msal_auth_client = ManagedIdentityClient(
                SystemAssignedManagedIdentity(),
                http_client=Session(),
            )
        else:
            authority_path = self._msal_configuration.TENANT_ID or "botframework.com"
            authority = f"https://login.microsoftonline.com/{authority_path}"

            if self._client_credential_cache:
                logger.info("Using cached client credentials for MSAL authentication.")
                pass
            elif self._msal_configuration.AUTH_TYPE == AuthTypes.client_secret:
                self._client_credential_cache = self._msal_configuration.CLIENT_SECRET
            elif self._msal_configuration.AUTH_TYPE == AuthTypes.certificate:
                with open(self._msal_configuration.CERT_KEY_FILE) as file:
                    logger.info(
                        "Loading certificate private key for MSAL authentication."
                    )
                    private_key = file.read()

                with open(self._msal_configuration.CERT_PEM_FILE) as file:
                    logger.info("Loading public certificate for MSAL authentication.")
                    public_certificate = file.read()

                # Create an X509 object and calculate the thumbprint
                logger.info("Calculating thumbprint for the public certificate.")
                cert = load_pem_x509_certificate(
                    data=bytes(public_certificate, "UTF-8"), backend=default_backend()
                )
                thumbprint = cert.fingerprint(hashes.SHA1()).hex()

                self._client_credential_cache = {
                    "thumbprint": thumbprint,
                    "private_key": private_key,
                }
            else:
                logger.error(
                    f"Unsupported authentication type: {self._msal_configuration.AUTH_TYPE}"
                )
                raise NotImplementedError("Authentication type not supported")

            msal_auth_client = ConfidentialClientApplication(
                client_id=self._msal_configuration.CLIENT_ID,
                authority=authority,
                client_credential=self._client_credential_cache,
            )

        return msal_auth_client

    @staticmethod
    def _uri_validator(url_str: str) -> tuple[bool, Optional[URI]]:
        try:
            result = urlparse(url_str)
            return all([result.scheme, result.netloc]), result
        except AttributeError:
            logger.error(f"URI parsing error for {url_str}")
            return False, None

    def _resolve_scopes_list(self, instance_url: URI, scopes=None) -> list[str]:
        if scopes:
            return scopes

        temp_list: list[str] = []
        for scope in self._msal_configuration.SCOPES:
            scope_placeholder = scope
            if "{instance}" in scope_placeholder.lower():
                scope_placeholder = scope_placeholder.replace(
                    "{instance}", f"{instance_url.scheme}://{instance_url.hostname}"
                )
            temp_list.append(scope_placeholder)
        logger.debug(f"Resolved scopes: {temp_list}")
        return temp_list

    # the call to MSAL is blocking, but in the future we want to create an asyncio task
    # to avoid this
    async def get_agentic_application_token(
        self, agent_app_instance_id: str
    ) -> Optional[str]:
        """Gets the agentic application token for the given agent application instance ID.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :return: The agentic application token, or None if not found.
        :rtype: Optional[str]
        """

        if not agent_app_instance_id:
            raise ValueError("Agent application instance Id must be provided.")

        logger.info(
            "Attempting to get agentic application token from agent_app_instance_id %s",
            agent_app_instance_id,
        )
        msal_auth_client = self._create_client_application()

        if isinstance(msal_auth_client, ConfidentialClientApplication):

            # https://github.dev/AzureAD/microsoft-authentication-library-for-dotnet
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                ["api://AzureAdTokenExchange/.default"],
                data={"fmi_path": agent_app_instance_id},
            )

            if auth_result_payload:
                return auth_result_payload.get("access_token")

        return None

    async def get_agentic_instance_token(
        self, agent_app_instance_id: str
    ) -> tuple[str, str]:
        """Gets the agentic instance token for the given agent application instance ID.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :return: A tuple containing the agentic instance token and the agent application token.
        :rtype: tuple[str, str]
        """

        if not agent_app_instance_id:
            raise ValueError("Agent application instance Id must be provided.")

        logger.info(
            "Attempting to get agentic instance token from agent_app_instance_id %s",
            agent_app_instance_id,
        )
        agent_token_result = await self.get_agentic_application_token(
            agent_app_instance_id
        )

        if not agent_token_result:
            logger.error(
                "Failed to acquire agentic instance token or agent token for agent_app_instance_id %s",
                agent_app_instance_id,
            )
            raise Exception(
                f"Failed to acquire agentic instance token or agent token for agent_app_instance_id {agent_app_instance_id}"
            )

        authority = (
            f"https://login.microsoftonline.com/{self._msal_configuration.TENANT_ID}"
        )

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token_result},
        )

        agentic_instance_token = instance_app.acquire_token_for_client(
            ["api://AzureAdTokenExchange/.default"]
        )

        if not agentic_instance_token:
            logger.error(
                "Failed to acquire agentic instance token or agent token for agent_app_instance_id %s",
                agent_app_instance_id,
            )
            raise Exception(
                f"Failed to acquire agentic instance token or agent token for agent_app_instance_id {agent_app_instance_id}"
            )

        # future scenario where we don't know the blueprint id upfront

        token = agentic_instance_token.get("access_token")
        if not token:
            logger.error(
                "Failed to acquire agentic instance token, %s", agentic_instance_token
            )
            raise ValueError(f"Failed to acquire token. {str(agentic_instance_token)}")

        logger.debug(_DeferredLogOfBlueprintId(token))

        return agentic_instance_token["access_token"], agent_token_result

    async def get_agentic_user_token(
        self, agent_app_instance_id: str, upn: str, scopes: list[str]
    ) -> Optional[str]:
        """Gets the agentic user token for the given agent application instance ID and user principal name and the scopes.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :param upn: The user principal name.
        :type upn: str
        :param scopes: The scopes to request for the token.
        :type scopes: list[str]
        :return: The agentic user token, or None if not found.
        :rtype: Optional[str]
        """
        if not agent_app_instance_id or not upn:
            raise ValueError(
                "Agent application instance Id and user principal name must be provided."
            )

        logger.info(
            "Attempting to get agentic user token from agent_app_instance_id %s and upn %s",
            agent_app_instance_id,
            upn,
        )
        instance_token, agent_token = await self.get_agentic_instance_token(
            agent_app_instance_id
        )

        if not instance_token or not agent_token:
            logger.error(
                "Failed to acquire instance token or agent token for agent_app_instance_id %s and upn %s",
                agent_app_instance_id,
                upn,
            )
            raise Exception(
                f"Failed to acquire instance token or agent token for agent_app_instance_id {agent_app_instance_id} and upn {upn}"
            )

        authority = (
            f"https://login.microsoftonline.com/{self._msal_configuration.TENANT_ID}"
        )

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token},
        )

        logger.info(
            "Acquiring agentic user token for agent_app_instance_id %s and upn %s",
            agent_app_instance_id,
            upn,
        )
        auth_result_payload = instance_app.acquire_token_for_client(
            scopes,
            data={
                "username": upn,
                "user_federated_identity_credential": instance_token,
                "grant_type": "user_fic",
            },
        )

        if not auth_result_payload:
            logger.error(
                "Failed to acquire agentic user token for agent_app_instance_id %s and upn %s, %s",
                agent_app_instance_id,
                upn,
                auth_result_payload,
            )
            return None

        access_token = auth_result_payload.get("access_token")
        if not access_token:
            logger.error(
                "Failed to acquire agentic user token for agent_app_instance_id %s and upn %s, %s",
                agent_app_instance_id,
                upn,
                auth_result_payload,
            )
            return None

        logger.info("Acquired agentic user token response.")
        return access_token
