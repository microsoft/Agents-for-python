# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from fastapi import Request


class FastApiRequestAdapter:
    """Adapter to make FastAPI Request compatible with HttpRequestProtocol."""

    def __init__(self, request: Request):
        self._request = request

    @property
    def method(self) -> str:
        return self._request.method

    @property
    def headers(self):
        return self._request.headers

    async def json(self):
        return await self._request.json()

    def get_claims_identity(self):
        return getattr(self._request.state, "claims_identity", None)

    def get_path_param(self, name: str) -> str:
        return self._request.path_params.get(name, "")
