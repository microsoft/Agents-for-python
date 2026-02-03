# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import re
import asyncio
import logging
import jwt
from typing import Optional
from urllib.parse import urlparse, ParseResult as URI
from msal import (
    ConfidentialClientApplication,
    ManagedIdentityClient,
    UserAssignedManagedIdentity,
    SystemAssignedManagedIdentity,
    TokenCache,
)
from requests import Session
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from microsoft_agents.activity._utils import _DeferredString

from microsoft_agents.hosting.core import (
    AuthTypes,
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)
from microsoft_agents.authentication.msal.errors import authentication_errors

logger = logging.getLogger(__name__)


async def _async_acquire_token_for_client(msal_auth_client, *args, **kwargs):
    """MSAL in Python does not support async, so we use asyncio.to_thread to run it in
    a separate thread and avoid blocking the event loop
    """
    return await asyncio.to_thread(
        lambda: msal_auth_client.acquire_token_for_client(*args, **kwargs)
    )


class MsalAuth(AccessTokenProviderBase):

    _client_credential_cache = None

    def __init__(self, msal_configuration: AgentAuthConfiguration):
        """Initializes the MsalAuth class with the given configuration.

        :param msal_configuration: The MSAL authentication configuration. Assumed to
            not be mutated after being passed in.
        :type msal_configuration: :class:`microsoft_agents.hosting.core.authorization.agent_auth_configuration.AgentAuthConfiguration`
        """

        self._msal_configuration = msal_configuration
        self._msal_auth_client_map: dict[
            str, ConfidentialClientApplication | ManagedIdentityClient
        ] = {}

        # TokenCache is thread-safe and async-safe per MSAL documentation
        self._token_cache = TokenCache()
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
            raise ValueError(str(authentication_errors.InvalidInstanceUrl))
        assert instance_uri is not None # for mypy

        local_scopes = self._resolve_scopes_list(instance_uri, scopes)
        msal_auth_client = self._get_client()

        if isinstance(msal_auth_client, ManagedIdentityClient):
            logger.info("Acquiring token using Managed Identity Client.")
            auth_result_payload = await _async_acquire_token_for_client(
                msal_auth_client, resource=resource_url
            )
        elif isinstance(msal_auth_client, ConfidentialClientApplication):
            logger.info("Acquiring token using Confidential Client Application.")
            auth_result_payload = await _async_acquire_token_for_client(
                msal_auth_client, scopes=local_scopes
            )
        else:
            auth_result_payload = None

        res = auth_result_payload.get("access_token") if auth_result_payload else None
        if not res:
            logger.error("Failed to acquire token for resource %s", auth_result_payload)
            raise ValueError(
                authentication_errors.FailedToAcquireToken.format(
                    str(auth_result_payload)
                )
            )

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

        msal_auth_client = self._get_client()
        if isinstance(msal_auth_client, ManagedIdentityClient):
            logger.error(
                "Attempted on-behalf-of flow with Managed Identity authentication."
            )
            raise NotImplementedError(
                str(authentication_errors.OnBehalfOfFlowNotSupportedManagedIdentity)
            )
        elif isinstance(msal_auth_client, ConfidentialClientApplication):
            # TODO: Handling token error / acquisition failed

            # MSAL in Python does not support async, so we use asyncio.to_thread to run it in
            # a separate thread and avoid blocking the event loop
            token = await asyncio.to_thread(
                lambda: msal_auth_client.acquire_token_on_behalf_of(
                    scopes=scopes, user_assertion=user_assertion
                )
            )

            if "access_token" not in token:
                logger.error(
                    f"Failed to acquire token on behalf of user: {user_assertion}"
                )
                raise ValueError(
                    authentication_errors.FailedToAcquireToken.format(str(token))
                )

            return token["access_token"]

        logger.error(
            f"On-behalf-of flow is not supported with the current authentication type: {msal_auth_client.__class__.__name__}"
        )
        raise NotImplementedError(
            authentication_errors.OnBehalfOfFlowNotSupportedAuthType.format(
                msal_auth_client.__class__.__name__
            )
        )

    @staticmethod
    def _resolve_authority(
        config: AgentAuthConfiguration, tenant_id: str | None = None
    ) -> str:
        tenant_id = MsalAuth._resolve_tenant_id(config, tenant_id)
        if not tenant_id:
            return (
                config.AUTHORITY
                or f"https://login.microsoftonline.com/{config.TENANT_ID}"
            )

        if config.AUTHORITY:
            return re.sub(r"/common(?=/|$)", f"/{tenant_id}", config.AUTHORITY)

        return f"https://login.microsoftonline.com/{tenant_id}"

    @staticmethod
    def _resolve_tenant_id(
        config: AgentAuthConfiguration, tenant_id: str | None = None
    ) -> str:

        if not config.TENANT_ID:
            if tenant_id:
                return tenant_id
            raise ValueError("TENANT_ID is not set in the configuration.")

        if tenant_id and config.TENANT_ID.lower() == "common":
            return tenant_id

        return config.TENANT_ID

    def _create_client_application(
        self, tenant_id: str | None = None
    ) -> ConfidentialClientApplication | ManagedIdentityClient:

        if self._msal_configuration.AUTH_TYPE == AuthTypes.user_managed_identity:
            return ManagedIdentityClient(
                UserAssignedManagedIdentity(
                    client_id=self._msal_configuration.CLIENT_ID
                ),
                http_client=Session(),
            )

        elif self._msal_configuration.AUTH_TYPE == AuthTypes.system_managed_identity:
            return ManagedIdentityClient(
                SystemAssignedManagedIdentity(),
                http_client=Session(),
            )
        else:
            authority = MsalAuth._resolve_authority(self._msal_configuration, tenant_id)

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
                raise NotImplementedError(
                    str(authentication_errors.AuthenticationTypeNotSupported)
                )

            return ConfidentialClientApplication(
                client_id=self._msal_configuration.CLIENT_ID,
                authority=authority,
                client_credential=self._client_credential_cache,
            )

    def _client_rep(
        self, tenant_id: str | None = None, instance_id: str | None = None
    ) -> str:
        # Create a unique representation for the client based on tenant_id and instance_id
        # instance_id None is for when no agentic instance is associated with the request.
        tenant_id = tenant_id or self._msal_configuration.TENANT_ID
        return f"tenant:{tenant_id}.instance:{instance_id}"

    def _get_client(
        self, tenant_id: str | None = None, instance_id: str | None = None
    ) -> ConfidentialClientApplication | ManagedIdentityClient:
        rep = self._client_rep(tenant_id, instance_id)
        if rep in self._msal_auth_client_map:
            return self._msal_auth_client_map[rep]
        else:
            client = self._create_client_application(tenant_id)
            self._msal_auth_client_map[rep] = client
            return client

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
        lst = self._msal_configuration.SCOPES or []
        for scope in lst:
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
        self, tenant_id: str, agent_app_instance_id: str
    ) -> Optional[str]:
        """Gets the agentic application token for the given agent application instance ID.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :return: The agentic application token, or None if not found.
        :rtype: Optional[str]
        """

        if not agent_app_instance_id:
            raise ValueError(
                str(authentication_errors.AgentApplicationInstanceIdRequired)
            )

        logger.info(
            "Attempting to get agentic application token from agent_app_instance_id %s",
            agent_app_instance_id,
        )
        msal_auth_client = self._get_client(tenant_id, agent_app_instance_id)

        if isinstance(msal_auth_client, ConfidentialClientApplication):

            # https://github.dev/AzureAD/microsoft-authentication-library-for-dotnet
            auth_result_payload = await _async_acquire_token_for_client(
                msal_auth_client,
                ["api://AzureAdTokenExchange/.default"],
                data={"fmi_path": agent_app_instance_id},
            )

            if auth_result_payload:
                return auth_result_payload.get("access_token")

        return None

    async def get_agentic_instance_token(
        self, tenant_id: str, agent_app_instance_id: str
    ) -> tuple[str, str]:
        """Gets the agentic instance token for the given agent application instance ID.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :return: A tuple containing the agentic instance token and the agent application token.
        :rtype: tuple[str, str]
        """

        if not agent_app_instance_id:
            raise ValueError(
                str(authentication_errors.AgentApplicationInstanceIdRequired)
            )

        logger.info(
            "Attempting to get agentic instance token from agent_app_instance_id %s",
            agent_app_instance_id,
        )
        agent_token_result = await self.get_agentic_application_token(
            tenant_id, agent_app_instance_id
        )

        if not agent_token_result:
            logger.error(
                "Failed to acquire agentic instance token or agent token for agent_app_instance_id %s",
                agent_app_instance_id,
            )
            raise Exception(
                authentication_errors.FailedToAcquireAgenticInstanceToken.format(
                    agent_app_instance_id
                )
            )

        authority = MsalAuth._resolve_authority(self._msal_configuration, tenant_id)

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token_result},
            token_cache=self._token_cache,
        )

        agentic_instance_token = await _async_acquire_token_for_client(
            instance_app, ["api://AzureAdTokenExchange/.default"]
        )

        if not agentic_instance_token:
            logger.error(
                "Failed to acquire agentic instance token or agent token for agent_app_instance_id %s",
                agent_app_instance_id,
            )
            raise Exception(
                authentication_errors.FailedToAcquireAgenticInstanceToken.format(
                    agent_app_instance_id
                )
            )

        # future scenario where we don't know the blueprint id upfront

        token = agentic_instance_token.get("access_token")
        if not token:
            logger.error(
                "Failed to acquire agentic instance token, %s", agentic_instance_token
            )
            raise ValueError(
                authentication_errors.FailedToAcquireToken.format(
                    str(agentic_instance_token)
                )
            )

        logger.debug(
            "Agentic blueprint id: %s",
            _DeferredString(
                lambda: jwt.decode(token, options={"verify_signature": False}).get(
                    "xms_par_app_azp"
                )
            ),
        )

        return agentic_instance_token["access_token"], agent_token_result

    async def get_agentic_user_token(
        self,
        tenant_id: str,
        agent_app_instance_id: str,
        agentic_user_id: str,
        scopes: list[str],
    ) -> Optional[str]:
        """Gets the agentic user token for the given agent application instance ID and agentic user Id and the scopes.

        :param agent_app_instance_id: The agent application instance ID.
        :type agent_app_instance_id: str
        :param agentic_user_id: The agentic user ID.
        :type agentic_user_id: str
        :param scopes: The scopes to request for the token.
        :type scopes: list[str]
        :return: The agentic user token, or None if not found.
        :rtype: Optional[str]
        """
        if not agent_app_instance_id or not agentic_user_id:
            raise ValueError(
                str(authentication_errors.AgentApplicationInstanceIdAndUserIdRequired)
            )

        logger.info(
            "Attempting to get agentic user token from agent_app_instance_id %s and agentic_user_id %s",
            agent_app_instance_id,
            agentic_user_id,
        )
        instance_token, agent_token = await self.get_agentic_instance_token(
            tenant_id, agent_app_instance_id
        )

        if not instance_token or not agent_token:
            logger.error(
                "Failed to acquire instance token or agent token for agent_app_instance_id %s and agentic_user_id %s",
                agent_app_instance_id,
                agentic_user_id,
            )
            raise Exception(
                authentication_errors.FailedToAcquireInstanceOrAgentToken.format(
                    agent_app_instance_id, agentic_user_id
                )
            )

        authority = MsalAuth._resolve_authority(self._msal_configuration, tenant_id)

        instance_app = ConfidentialClientApplication(
            client_id=agent_app_instance_id,
            authority=authority,
            client_credential={"client_assertion": agent_token},
            token_cache=self._token_cache,
        )

        logger.info(
            "Acquiring agentic user token for agent_app_instance_id %s and agentic_user_id %s",
            agent_app_instance_id,
            agentic_user_id,
        )
        # MSAL in Python does not support async, so we use asyncio.to_thread to run it in
        # a separate thread and avoid blocking the event loop
        auth_result_payload = await _async_acquire_token_for_client(
            instance_app,
            scopes,
            data={
                "user_id": agentic_user_id,
                "user_federated_identity_credential": instance_token,
                "grant_type": "user_fic",
            },
        )

        if not auth_result_payload:
            logger.error(
                "Failed to acquire agentic user token for agent_app_instance_id %s and agentic_user_id %s, %s",
                agent_app_instance_id,
                agentic_user_id,
                auth_result_payload,
            )
            return None

        access_token = auth_result_payload.get("access_token")
        if not access_token:
            logger.error(
                "Failed to acquire agentic user token for agent_app_instance_id %s and agentic_user_id %s, %s",
                agent_app_instance_id,
                agentic_user_id,
                auth_result_payload,
            )
            return None

        logger.info("Acquired agentic user token response.")
        return access_token
