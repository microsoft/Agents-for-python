from typing import Any, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

from microsoft_agents.hosting.core import (
    ChannelServiceClientFactoryBase,
    CloudAdapterBase,
    Connections,
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
        return getattr(
            request.state, "claims_identity", self._default_claims_identity()
        )

    def _method_not_allowed_error(self, request: Request) -> Exception:
        return HTTPException(status_code=405, detail="Method Not Allowed")

    def _unsupported_media_type_error(self, request: Request) -> Exception:
        return HTTPException(status_code=415, detail="Unsupported Media Type")

    def _bad_request_error(self, request: Request) -> Exception:
        return HTTPException(status_code=400, detail="Bad Request")

    def _unauthorized_error(self, request: Request) -> Exception:
        return HTTPException(status_code=401, detail="Unauthorized")

    def _create_invoke_response(
        self, request: Request, invoke_response: Any
    ) -> Response:
        return JSONResponse(
            content=invoke_response.body,
            status_code=invoke_response.status,
        )

    def _create_accepted_response(self, request: Request) -> Response:
        return Response(status_code=202)
