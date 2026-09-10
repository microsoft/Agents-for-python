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
from microsoft_agents.hosting.core import (
    AccessTokenProviderBase,
    ClaimsIdentity,
    Connections,
    TurnContext,
)
from microsoft_agents.hosting.core.app.m365_attachment_downloader import (
    M365AttachmentDownloader,
)
from microsoft_agents.hosting.core.outbound_host_validator import OutboundHostValidator


class _FakeTokenProvider(AccessTokenProviderBase):
    def __init__(self, name: str):
        self.name = name
        self.requested: tuple[str, list[str]] | None = None

    @property
    def configuration(self):
        return None

    async def get_access_token(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        self.requested = (resource_url, scopes)
        return f"{self.name}-token"

    async def acquire_token_on_behalf_of(
        self, scopes: list[str], user_assertion: str
    ) -> str:
        return f"{self.name}-obo-token"


class _FakeConnections(Connections):
    def __init__(self, provider: AccessTokenProviderBase | None):
        self._provider = provider

    def get_connection(self, connection_name: str) -> AccessTokenProviderBase:
        if self._provider is None:
            raise ValueError("no connection configured")
        return self._provider

    def get_default_connection(self) -> AccessTokenProviderBase:
        return self._provider

    def get_token_provider(
        self, claims_identity, service_url
    ) -> AccessTokenProviderBase:
        return self._provider

    def get_token_provider_from_activity(
        self, claims_identity, activity
    ) -> AccessTokenProviderBase:
        return self._provider

    def get_default_connection_configuration(self):
        return None


def _make_claims_identity() -> ClaimsIdentity:
    return ClaimsIdentity(claims={"aud": "test-audience"}, authentication_type="test")


def _make_context(
    channel_id: str = "msteams",
    attachments: list[Attachment] | None = None,
    identity: ClaimsIdentity | None = None,
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
    return TurnContext(
        MagicMock(),
        activity,
        identity=identity if identity is not None else _make_claims_identity(),
    )


class _FakeResponse:
    def __init__(self, status: int, content: bytes, content_type: str):
        self.status = status
        self._content = content
        self.headers = {"Content-Type": content_type}
        self.request_headers: dict | None = None

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

    def get(self, url: str, headers=None, **kwargs) -> _FakeResponse:
        self.requested_urls.append(url)
        self._response.request_headers = headers
        return self._response

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args) -> bool:
        return False


class TestM365AttachmentDownloaderChannelAndValidation:
    @pytest.mark.asyncio
    async def test_raises_when_context_has_no_identity(self):
        downloader = M365AttachmentDownloader(connections=_FakeConnections(None))
        activity = Activity(
            type="message",
            id="1234",
            channel_id="msteams",
            from_property=ChannelAccount(id="user", name="User Name"),
            recipient=ChannelAccount(id="bot", name="Bot Name"),
            conversation=ConversationAccount(id="convo", name="Convo Name"),
            service_url="https://example.org",
        )
        context = TurnContext(MagicMock(), activity, identity=None)

        with pytest.raises(ValueError):
            await downloader.download_files(context)

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_non_teams_channel(self):
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p"))
        )
        context = _make_context(
            channel_id="webchat",
            attachments=[
                Attachment(
                    content_type="image/png", content_url="https://example.org/a.png"
                )
            ],
        )

        assert await downloader.download_files(context) == []

    @pytest.mark.asyncio
    async def test_allows_m365_copilot_channel(self):
        response = _FakeResponse(
            status=200, content=b"bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p")),
            client_factory=lambda: session,
        )
        context = _make_context(
            channel_id="msteams:COPILOT",
            attachments=[
                Attachment(
                    content_type="text/plain", content_url="https://example.org/a.txt"
                )
            ],
        )

        files = await downloader.download_files(context)

        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_attachments(self):
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p"))
        )
        context = _make_context(attachments=None)

        assert await downloader.download_files(context) == []

    @pytest.mark.asyncio
    async def test_filters_out_html_attachments(self):
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p"))
        )
        context = _make_context(
            attachments=[Attachment(content_type="text/html", content="<p>hi</p>")]
        )

        assert await downloader.download_files(context) == []


class TestM365AttachmentDownloaderInlineContent:
    @pytest.mark.asyncio
    async def test_downloads_inline_content_as_json_bytes(self):
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p"))
        )
        attachment = Attachment(
            content_type="application/vnd.custom",
            content={"foo": "bar"},
            name="data.json",
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert files[0].content == bytes(json.dumps({"foo": "bar"}), "utf-8")
        assert files[0].filename == "data.json"


class TestM365AttachmentDownloaderRemoteContent:
    @pytest.mark.asyncio
    async def test_downloads_remote_file_using_download_url_from_content(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        token_provider = _FakeTokenProvider("p")
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(token_provider), client_factory=lambda: session
        )
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://example.org/file.txt",
            content={"downloadUrl": "https://example.org/real-download"},
            name="file.txt",
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert files[0].content == b"file-bytes"
        assert files[0].content_url == "https://example.org/file.txt"
        assert session.requested_urls == ["https://example.org/real-download"]

    @pytest.mark.asyncio
    async def test_falls_back_to_content_url_when_download_url_missing(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p")),
            client_factory=lambda: session,
        )
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://example.org/file.txt",
            content={"someOtherKey": "value"},
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert session.requested_urls == ["https://example.org/file.txt"]

    @pytest.mark.asyncio
    async def test_normalizes_image_content_type_to_png(self):
        response = _FakeResponse(
            status=200, content=b"\x89PNG", content_type="image/jpeg"
        )
        session = _FakeSession(response)
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p")),
            client_factory=lambda: session,
        )
        attachment = Attachment(
            content_type="image/jpeg", content_url="https://example.org/pic.jpg"
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert files[0].content_type == "image/png"

    @pytest.mark.asyncio
    async def test_returns_none_entry_for_failed_status(self):
        response = _FakeResponse(status=404, content=b"", content_type="text/plain")
        session = _FakeSession(response)
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p")),
            client_factory=lambda: session,
        )
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
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(_FakeTokenProvider("p")),
            client_factory=lambda: session,
            host_validator=host_validator,
        )
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://example.org/file.txt",
            content={"downloadUrl": "https://evil.example.com/relay"},
        )
        context = _make_context(attachments=[attachment])

        assert await downloader.download_files(context) == []
        assert session.requested_urls == []

    @pytest.mark.asyncio
    async def test_uses_anonymous_mode_without_requesting_token(self):
        response = _FakeResponse(
            status=200, content=b"file-bytes", content_type="text/plain"
        )
        session = _FakeSession(response)
        token_provider = _FakeTokenProvider("p")
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(token_provider),
            client_factory=lambda: session,
            use_anonymous=True,
        )
        attachment = Attachment(
            content_type="text/plain", content_url="https://example.org/file.txt"
        )
        context = _make_context(attachments=[attachment])

        files = await downloader.download_files(context)

        assert len(files) == 1
        assert token_provider.requested is None

    @pytest.mark.asyncio
    async def test_uses_named_token_provider_when_configured(self):
        named_provider = _FakeTokenProvider("named")
        downloader = M365AttachmentDownloader(
            connections=_FakeConnections(named_provider),
            client_factory=lambda: _FakeSession(
                _FakeResponse(status=200, content=b"bytes", content_type="text/plain")
            ),
            token_provider_name="named-connection",
        )
        attachment = Attachment(
            content_type="text/plain", content_url="https://example.org/file.txt"
        )
        context = _make_context(attachments=[attachment])

        await downloader.download_files(context)

        assert named_provider.requested is not None

    @pytest.mark.asyncio
    async def test_raises_when_no_token_provider_can_be_resolved(self):
        downloader = M365AttachmentDownloader(connections=_FakeConnections(None))
        attachment = Attachment(
            content_type="text/plain", content_url="https://example.org/file.txt"
        )
        context = _make_context(attachments=[attachment])

        with pytest.raises(RuntimeError):
            await downloader.download_files(context)
