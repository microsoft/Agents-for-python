# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from aiohttp.web import Request


class AiohttpRequestAdapter:
    """Adapter to make aiohttp Request compatible with HttpRequestProtocol."""

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
        return self._request.get("claims_identity")

    def get_path_param(self, name: str) -> str:
        return self._request.match_info[name]
