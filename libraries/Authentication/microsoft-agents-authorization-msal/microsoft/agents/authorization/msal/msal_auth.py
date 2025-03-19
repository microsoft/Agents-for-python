from __future__ import annotations

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

from microsoft.agents.authentication import AccessTokenProviderBase

from .auth_types import AuthTypes
from .msal_auth_configuration import MsalAuthConfiguration


class MsalAuth(AccessTokenProviderBase):

    _client_credential_cache = None

    def __init__(self, msal_configuration: MsalAuthConfiguration):
        self._msal_configuration = msal_configuration

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        valid_uri, instance_uri = self._uri_validator(resource_url)
        if not valid_uri:
            raise ValueError("Invalid instance URL")

        local_scopes = self._resolve_scopes_list(instance_uri, scopes)
        msal_auth_client = self._create_client_application()

        if isinstance(msal_auth_client, ManagedIdentityClient):
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                resource=resource_url
            )
        elif isinstance(msal_auth_client, ConfidentialClientApplication):
            auth_result_payload = msal_auth_client.acquire_token_for_client(
                scopes=local_scopes
            )

        # TODO: Handling token error / acquisition failed
        return auth_result_payload["access_token"]

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
                pass
            elif self._msal_configuration.AUTH_TYPE == AuthTypes.client_secret:
                self._client_credential_cache = self._msal_configuration.CLIENT_SECRET
            elif self._msal_configuration.AUTH_TYPE == AuthTypes.certificate:
                with open(self._msal_configuration.CERT_KEY_FILE) as file:
                    private_key = file.read()

                with open(self._msal_configuration.CERT_PEM_FILE) as file:
                    public_certificate = file.read()

                # Create an X509 object and calculate the thumbprint
                cert = load_pem_x509_certificate(
                    data=bytes(public_certificate, "UTF-8"), backend=default_backend()
                )
                thumbprint = cert.fingerprint(hashes.SHA1()).hex()

                self._client_credential_cache = {
                    "thumbprint": thumbprint,
                    "private_key": private_key,
                }
            else:
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
        return temp_list
