# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer


@dataclass
class DownloadServer:
    server: TestServer
    requested_paths: list[str] = field(default_factory=list)

    def url(self, path: str) -> str:
        return str(self.server.make_url(path))


@pytest.fixture
async def download_server():
    requested_paths: list[str] = []

    async def download(request: web.Request) -> web.Response:
        requested_paths.append(request.path)

        if request.match_info["filename"] == "missing.txt":
            raise web.HTTPNotFound()
        if request.match_info["filename"] == "photo.jpg":
            return web.Response(body=b"image-content", content_type="image/jpeg")
        if request.match_info["filename"] == "empty-content-type.txt":
            return web.Response(
                body=b"untyped-content",
                headers={"Content-Type": ""},
            )
        return web.Response(body=b"document-content", content_type="text/plain")

    app = web.Application()
    app.router.add_get("/files/{filename}", download)
    server = TestServer(app, host="localhost")
    await server.start_server()

    try:
        yield DownloadServer(server=server, requested_paths=requested_paths)
    finally:
        await server.close()
