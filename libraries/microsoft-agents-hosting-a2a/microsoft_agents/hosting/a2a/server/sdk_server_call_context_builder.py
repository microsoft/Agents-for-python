# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.server.context import ServerCallContext
from a2a.server.routes import DefaultServerCallContextBuilder
from a2a.extensions.common import (
    HTTP_EXTENSION_HEADER,
    get_requested_extensions,
)

from starlette.requests import Request

from ._constants import _CLAIMS_IDENTITY_KEY

class SDKServerCallContextBuilder(DefaultServerCallContextBuilder):
    """A default implementation of ServerCallContextBuilder."""

    def build(self, request: Request) -> ServerCallContext:
        """Builds a ServerCallContext from a Starlette Request.

        Args:
            request: The incoming Starlette Request object.

        Returns:
            A ServerCallContext instance populated with user and state
            information from the request.
        """
        state = {}
        if "auth" in request.scope:
            state["auth"] = request.auth
        state["headers"] = dict(request.headers)

        if getattr(request.state, "claims_identity", None) is not None:
            state[_CLAIMS_IDENTITY_KEY] = request.state.claims_identity

        return ServerCallContext(
            user=self.build_user(request),
            state=state,
            requested_extensions=get_requested_extensions(
                request.headers.getlist(HTTP_EXTENSION_HEADER)
            ),
        )
