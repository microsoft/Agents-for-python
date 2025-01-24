# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.10.3, generator: @autorest/python@6.27.0)
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from copy import deepcopy
from typing import Any, Awaitable
from typing_extensions import Self

from azure.core import AsyncPipelineClient
from azure.core.credentials import AzureKeyCredential
from azure.core.pipeline import policies
from azure.core.rest import AsyncHttpResponse, HttpRequest

from ._user_token_client_configuration import TokenConfiguration
from .operations import (
    BotSignInOperations,
    TokenInternalsOperations,
    UserTokenOperations,
)
from .._serialization import Deserializer, Serializer
from ..bot_sign_in_base import BotSignInBase
from ..user_token_base import UserTokenBase
from ..user_token_client_base import UserTokenClientBase


class UserTokenClient(
    UserTokenClientBase
):  # pylint: disable=client-accepts-api-version-keyword
    """Token.

    :ivar bot_sign_in: BotSignInOperations operations
    :vartype bot_sign_in: microsoft.agents.connector.operations.BotSignInOperations
    :ivar user_token: UserTokenOperations operations
    :vartype user_token: microsoft.agents.connector.operations.UserTokenOperations
    :ivar token_internals: TokenInternalsOperations operations
    :vartype token_internals:
     microsoft.agents.connector.operations.TokenInternalsOperations
    :param credential: Credential needed for the client to connect to Azure. Required.
    :type credential: ~azure.core.credentials.AzureKeyCredential
    :keyword endpoint: Service URL. Required. Default value is "".
    :paramtype endpoint: str
    """

    def __init__(
        self, credential: AzureKeyCredential, *, endpoint: str = "", **kwargs: Any
    ) -> None:
        self._config = TokenConfiguration(credential=credential, **kwargs)
        _policies = kwargs.pop("policies", None)
        if _policies is None:
            _policies = [
                policies.RequestIdPolicy(**kwargs),
                self._config.headers_policy,
                self._config.user_agent_policy,
                self._config.proxy_policy,
                policies.ContentDecodePolicy(**kwargs),
                self._config.redirect_policy,
                self._config.retry_policy,
                self._config.authentication_policy,
                self._config.custom_hook_policy,
                self._config.logging_policy,
                policies.DistributedTracingPolicy(**kwargs),
                (
                    policies.SensitiveHeaderCleanupPolicy(**kwargs)
                    if self._config.redirect_policy
                    else None
                ),
                self._config.http_logging_policy,
            ]
        self._client: AsyncPipelineClient = AsyncPipelineClient(
            base_url=endpoint, policies=_policies, **kwargs
        )

        self._serialize = Serializer()
        self._deserialize = Deserializer()
        self._serialize.client_side_validation = False
        self.bot_sign_in = BotSignInOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.user_token = UserTokenOperations(
            self._client, self._config, self._serialize, self._deserialize
        )
        self.token_internals = TokenInternalsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )

    @property
    def bot_sign_in(self) -> BotSignInBase:
        return self.bot_sign_in

    @property
    def user_token(self) -> UserTokenBase:
        return self.user_token

    def send_request(
        self, request: HttpRequest, *, stream: bool = False, **kwargs: Any
    ) -> Awaitable[AsyncHttpResponse]:
        """Runs the network request through the client's chained policies.

        >> from azure.core.rest import HttpRequest
        >> request = HttpRequest("GET", "https://www.example.org/")
        <HttpRequest [GET], url: 'https://www.example.org/'>
        >> response = await client.send_request(request)
        <AsyncHttpResponse: 200 OK>

        For more information on this code flow, see https://aka.ms/azsdk/dpcodegen/python/send_request

        :param request: The network request you want to make. Required.
        :type request: ~azure.core.rest.HttpRequest
        :keyword bool stream: Whether the response payload will be streamed. Defaults to False.
        :return: The response of your network call. Does not do error handling on your response.
        :rtype: ~azure.core.rest.AsyncHttpResponse
        """

        request_copy = deepcopy(request)
        request_copy.url = self._client.format_url(request_copy.url)
        return self._client.send_request(request_copy, stream=stream, **kwargs)  # type: ignore

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_details: Any) -> None:
        await self._client.__aexit__(*exc_details)
