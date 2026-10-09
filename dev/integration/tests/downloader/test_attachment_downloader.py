# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

import pytest

from microsoft_agents.activity import Attachment, Channels
from microsoft_agents.hosting.core import OutboundHostValidator
from microsoft_agents.hosting.core.app.attachment_downloader import (
    AttachmentDownloader,
)
from microsoft_agents.hosting.testing import AgentClient, AgentEnvironment

from .conftest import DownloadServer
from .scenario import DOWNLOADER_SCENARIO, download_attachments


@pytest.mark.agent_test(DOWNLOADER_SCENARIO)
class TestAttachmentDownloader:
    async def test_downloads_file_from_local_http_server(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        content_url = download_server.url("/files/document.txt")
        attachment = Attachment(
            content_type="text/plain",
            content_url=content_url,
            name="document.txt",
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=[attachment],
        )

        assert files == [
            {
                "content": "document-content",
                "content_type": "text/plain",
                "content_url": content_url,
                "filename": "document.txt",
            }
        ]
        assert download_server.requested_paths == ["/files/document.txt"]

    async def test_ignores_remote_file_when_server_returns_not_found(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url=download_server.url("/files/missing.txt"),
            name="missing.txt",
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=[attachment],
        )

        assert files == []
        assert download_server.requested_paths == ["/files/missing.txt"]

    async def test_leaves_teams_attachments_for_the_m365_downloader(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url=download_server.url("/files/document.txt"),
            name="document.txt",
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files == []
        assert download_server.requested_paths == []

    async def test_downloads_mixed_attachment_batch_in_original_order(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        remote_url = download_server.url("/files/document.txt")
        attachments = [
            Attachment(
                content_type="text/plain",
                content_url=remote_url,
                name="remote.txt",
            ),
            Attachment(
                content_type="text/plain",
                content_url=download_server.url("/files/missing.txt"),
                name="missing.txt",
            ),
            Attachment(
                content_type="application/json",
                content={"source": "inline"},
                name="inline.json",
            ),
        ]

        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=attachments,
        )

        assert files == [
            {
                "content": "document-content",
                "content_type": "text/plain",
                "content_url": remote_url,
                "filename": "remote.txt",
            },
            {
                "content": json.dumps({"source": "inline"}),
                "content_type": "application/json",
                "content_url": None,
                "filename": "inline.json",
            },
        ]
        assert download_server.requested_paths == [
            "/files/document.txt",
            "/files/missing.txt",
        ]

    async def test_normalizes_downloaded_image_content_type_to_png(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        content_url = download_server.url("/files/photo.jpg")

        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=[
                Attachment(
                    content_type="image/jpeg",
                    content_url=content_url,
                    name="photo.jpg",
                )
            ],
        )

        assert files[0]["content_type"] == "image/png"
        assert download_server.requested_paths == ["/files/photo.jpg"]

    async def test_serializes_inline_attachment_content_as_json(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
    ):
        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=[
                Attachment(
                    content_type="application/vnd.example",
                    content={"message": "hello"},
                    name="payload.json",
                )
            ],
        )

        assert files == [
            {
                "content": json.dumps({"message": "hello"}),
                "content_type": "application/vnd.example",
                "content_url": None,
                "filename": "payload.json",
            }
        ]

    async def test_blocks_remote_file_rejected_by_host_validator(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        downloader = AttachmentDownloader(
            host_validator=OutboundHostValidator(
                enabled=True,
                hosts=["allowed.example"],
                include_default_microsoft_hosts=False,
            )
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.webchat,
            attachments=[
                Attachment(
                    content_type="text/plain",
                    content_url=download_server.url("/files/document.txt"),
                    name="document.txt",
                )
            ],
        )

        assert files == []
        assert download_server.requested_paths == []

    async def test_reports_empty_response_content_type(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        files = await download_attachments(
            agent_client,
            agent_environment,
            AttachmentDownloader(),
            channel_id=Channels.webchat,
            attachments=[
                Attachment(
                    content_type="text/plain",
                    content_url=download_server.url(
                        "/files/empty-content-type.txt"
                    ),
                    name="empty-content-type.txt",
                )
            ],
        )

        assert files[0]["content_type"] == ""
        assert download_server.requested_paths == [
            "/files/empty-content-type.txt"
        ]
