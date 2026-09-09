# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
from unittest.mock import MagicMock

import pytest

from microsoft_agents.activity import (
    Activity,
    Attachment,
    ChannelAccount,
    ConversationAccount,
)
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.core.app.attachment_downloader import AttachmentDownloader
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator


def _make_context(
    channel_id: str = "test", attachments: list[Attachment] | None = None
) -> TurnContext:
    kwargs = {}
    if attachments is not None:
        kwargs["attachments"] = attachments
    activity = Activity(
        type="message",
        id="1234",
        channel_id=channel_id,
        from_property=ChannelAccount(id="user", name="User Name"),
        recipient=ChannelAccount(id="bot", name="Bot Name"),
        conversation=ConversationAccount(id="convo", name="Convo Name"),
        service_url="https://example.org",
        **kwargs,
    )
    return TurnContext(MagicMock(), activity)


class _FakeResponse:
    def __init__(self, status: int, content: bytes, content_type: str):
        self.status = status
        self._content = content
        self.headers = {"Content-Type": content_type}

    async def read(self) -> bytes:
        return self._content

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *args) -> bool:
        return False


class _FakeSession:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.requested_urls: list[str] = []

    def get(self, url: str, **kwargs) -> _FakeResponse:
        self.requested_urls.append(url)
        return self._response

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args) -> bool:
        return False


class TestAttachmentDownloaderChannelAndEmptyCases:
    @pytest.mark.asyncio
    async def test_returns_empty_list_for_teams_channel(self):
        downloader = AttachmentDownloader()
        context = _make_context(
            channel_id="msteams",
            attachments=[
                Attachment(
                    content_type="image/png", content_url="https://example.org/a.png"
                )
            ],
        )

        assert await downloader.download_files(context) == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_attachments(self):
        downloader = AttachmentDownloader()
        context = _make_context(channel_id="test", attachments=None)

        assert await downloader.download_files(context) == []


class TestAttachmentDownloaderInlineContent:
    @pytest.mark.asyncio
    async def test_downloads_inline_content_as_json_bytes(self):
        downloader = AttachmentDownloader()
        attachment = Attachment(
            content_type="application/vnd.custom",
            content={"foo": "bar"},
            name="data.json",
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert files[0].content == bytes(json.dumps({"foo": "bar"}), "utf-8")
        assert files[0].content_type == "application/vnd.custom"
        assert files[0].filename == "data.json"


class TestAttachmentDownloaderRemoteContent:
    @pytest.mark.asyncio
    async def test_downloads_remote_file_and_returns_input_file(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        downloader = AttachmentDownloader(client_factory=lambda: session)
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://example.org/file.txt",
            name="file.txt",
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert files[0].content == b"file-bytes"
        assert files[0].content_type == "text/plain"
        assert files[0].content_url == "https://example.org/file.txt"
        assert files[0].filename == "file.txt"
        assert session.requested_urls == ["https://example.org/file.txt"]

    @pytest.mark.asyncio
    async def test_allows_http_localhost_urls(self):
        response = _FakeResponse(
            status=200, content=b"local-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        downloader = AttachmentDownloader(client_factory=lambda: session)
        attachment = Attachment(
            content_type="text/plain", content_url="http://localhost:3000/file.txt"
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_normalizes_image_content_type_to_png(self):
        response = _FakeResponse(
            status=200, content=b"\x89PNG", content_type="image/jpeg"
        )
        session = _FakeSession(response)
        downloader = AttachmentDownloader(client_factory=lambda: session)
        attachment = Attachment(
            content_type="image/jpeg", content_url="https://example.org/pic.jpg"
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert files[0].content_type == "image/png"

    @pytest.mark.asyncio
    async def test_returns_none_for_non_success_status(self):
        response = _FakeResponse(status=404, content=b"", content_type="text/plain")
        session = _FakeSession(response)
        downloader = AttachmentDownloader(client_factory=lambda: session)
        attachment = Attachment(
            content_type="text/plain", content_url="https://example.org/missing.txt"
        )
        context = _make_context(attachments=[attachment])

        assert await downloader.download_files(context) == []

    @pytest.mark.asyncio
    async def test_skips_disallowed_hosts_when_host_validator_enabled(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        host_validator = OutboundHostValidator(enabled=True, hosts=["contoso.com"])
        downloader = AttachmentDownloader(
            client_factory=lambda: session, host_validator=host_validator
        )
        attachment = Attachment(
            content_type="text/plain", content_url="https://evil.example.com/file.txt"
        )
        context = _make_context(attachments=[attachment])

        assert await downloader.download_files(context) == []
        assert session.requested_urls == []

    @pytest.mark.asyncio
    async def test_allows_permitted_hosts_when_host_validator_enabled(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        host_validator = OutboundHostValidator(enabled=True, hosts=["contoso.com"])
        downloader = AttachmentDownloader(
            client_factory=lambda: session, host_validator=host_validator
        )
        attachment = Attachment(
            content_type="text/plain", content_url="https://contoso.com/file.txt"
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
