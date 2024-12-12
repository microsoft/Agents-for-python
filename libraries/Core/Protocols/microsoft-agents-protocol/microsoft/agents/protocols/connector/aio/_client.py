# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.10.3, generator: @autorest/python@6.27.0)
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------

from copy import deepcopy
from typing import Any, Awaitable
from typing_extensions import Self

from azure.core import AsyncPipelineClient
from azure.core.pipeline import policies
from azure.core.rest import AsyncHttpResponse, HttpRequest

from .._serialization import Deserializer, Serializer
from ._configuration import ConnectorConfiguration
from .operations import AttachmentsOperations, ConnectorInternalsOperations, ConversationsOperations


class Connector:  # pylint: disable=client-accepts-api-version-keyword
    """The Azure Bot Service Connector APIs allow bots to send and receive
    messages, button clicks, and other programmatic events when connecting with
    end users. This API also includes facilities to get conversation metadata
    and perform other operations (deletions and content editing). This REST API
    may be used directly over HTTP and Web Socket, but is easiest to use with
    the Azure SDK ConnectorClient.

    © 2020 Microsoft.

    :ivar attachments: AttachmentsOperations operations
    :vartype attachments: Microsoft.Agents.Protocols.Connector.aio.operations.AttachmentsOperations
    :ivar conversations: ConversationsOperations operations
    :vartype conversations:
     Microsoft.Agents.Protocols.Connector.aio.operations.ConversationsOperations
    :ivar connector_internals: ConnectorInternalsOperations operations
    :vartype connector_internals:
     Microsoft.Agents.Protocols.Connector.aio.operations.ConnectorInternalsOperations
    :keyword endpoint: Service URL. Required. Default value is "".
    :paramtype endpoint: str
    """

    def __init__(  # pylint: disable=missing-client-constructor-parameter-credential
        self, *, endpoint: str = "", **kwargs: Any
    ) -> None:
        self._config = ConnectorConfiguration(**kwargs)
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
                policies.SensitiveHeaderCleanupPolicy(**kwargs) if self._config.redirect_policy else None,
                self._config.http_logging_policy,
            ]
        self._client: AsyncPipelineClient = AsyncPipelineClient(base_url=endpoint, policies=_policies, **kwargs)

        self._serialize = Serializer()
        self._deserialize = Deserializer()
        self._serialize.client_side_validation = False
        self.attachments = AttachmentsOperations(self._client, self._config, self._serialize, self._deserialize)
        self.conversations = ConversationsOperations(self._client, self._config, self._serialize, self._deserialize)
        self.connector_internals = ConnectorInternalsOperations(
            self._client, self._config, self._serialize, self._deserialize
        )

    def send_request(
        self, request: HttpRequest, *, stream: bool = False, **kwargs: Any
    ) -> Awaitable[AsyncHttpResponse]:
        """Runs the network request through the client's chained policies.

        >>> from azure.core.rest import HttpRequest
        >>> request = HttpRequest("GET", "https://www.example.org/")
        <HttpRequest [GET], url: 'https://www.example.org/'>
        >>> response = await client.send_request(request)
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
