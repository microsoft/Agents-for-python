from typing import Any, Optional

from aiohttp.web import (
    HTTPBadRequest,
    HTTPMethodNotAllowed,
    HTTPUnauthorized,
    HTTPUnsupportedMediaType,
    Request,
    Response,
    json_response,
)

from microsoft_agents.hosting.core import (
    CloudAdapterBase,
    Connections,
    ChannelServiceClientFactoryBase,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity

from .agent_http_adapter import AgentHttpAdapter


class CloudAdapter(CloudAdapterBase[Request, Response], AgentHttpAdapter):
    def __init__(
        self,
        *,
        connection_manager: Connections | None = None,
        channel_service_client_factory: ChannelServiceClientFactoryBase | None = None,
    ) -> None:
        super().__init__(
            connection_manager=connection_manager,
            channel_service_client_factory=channel_service_client_factory,
        )

    def _get_method(self, request: Request) -> str:
        return request.method

    async def _read_json_body(self, request: Request) -> Any:
        if "application/json" not in request.headers.get("Content-Type", ""):
            raise self._unsupported_media_type_error(request)
        return await request.json()

    def _get_claims_identity(self, request: Request) -> ClaimsIdentity | None:
        return request.get("claims_identity", self._default_claims_identity())

    def _method_not_allowed_error(self, request: Request) -> Exception:
        return HTTPMethodNotAllowed(request.method, ["POST"])

    def _unsupported_media_type_error(self, request: Request) -> Exception:
        return HTTPUnsupportedMediaType()

    def _bad_request_error(self, request: Request) -> Exception:
        return HTTPBadRequest()

    def _unauthorized_error(self, request: Request) -> Exception:
        return HTTPUnauthorized()

    def _create_invoke_response(
        self, request: Request, invoke_response: Any
    ) -> Response:
        return json_response(
            data=invoke_response.body,
            status=invoke_response.status,
        )

    def _create_accepted_response(self, request: Request) -> Response:
        return Response(status=202)
