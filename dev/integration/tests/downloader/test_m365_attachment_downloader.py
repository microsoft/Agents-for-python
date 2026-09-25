# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Attachment, Channels
from microsoft_agents.hosting.core import OutboundHostValidator
from microsoft_agents.hosting.core.app.attachment_downloader import (
    AttachmentDownloader,
)
from microsoft_agents.hosting.core.app.m365_attachment_downloader import (
    M365AttachmentDownloader,
)
from microsoft_agents.hosting.testing import AgentClient, AgentEnvironment

from .conftest import DownloadServer
from .scenario import DOWNLOADER_SCENARIO, download_attachments


@pytest.mark.agent_test(DOWNLOADER_SCENARIO)
class TestM365AttachmentDownloader:
    async def test_downloads_file_using_m365_download_url(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        original_content_url = "https://attachments.example/document.txt"
        attachment = Attachment(
            content_type="text/plain",
            content_url=original_content_url,
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="document.txt",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files == [
            {
                "content": "document-content",
                "content_type": "text/plain",
                "content_url": original_content_url,
                "filename": "document.txt",
            }
        ]
        assert download_server.requested_paths == ["/files/document.txt"]

    async def test_filters_html_attachments_without_downloading_them(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/html",
            content_url="https://attachments.example/card.html",
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="card.html",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files == []
        assert download_server.requested_paths == []

    async def test_blocks_download_url_rejected_by_host_validator(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://attachments.example/document.txt",
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="document.txt",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
            host_validator=OutboundHostValidator(
                enabled=True,
                hosts=["allowed.example"],
                include_default_microsoft_hosts=False,
            ),
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files == []
        assert download_server.requested_paths == []

    async def test_normalizes_downloaded_image_content_type_to_png(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="image/jpeg",
            content_url="https://attachments.example/photo.jpg",
            content={
                "downloadUrl": download_server.url("/files/photo.jpg"),
            },
            name="photo.jpg",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files[0]["content_type"] == "image/png"
        assert download_server.requested_paths == ["/files/photo.jpg"]

    async def test_falls_back_to_attachment_content_url(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        content_url = download_server.url("/files/document.txt")
        attachment = Attachment(
            content_type="text/plain",
            content_url=content_url,
            content={"source": "m365"},
            name="document.txt",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert files[0]["content"] == "document-content"
        assert files[0]["content_url"] == content_url
        assert download_server.requested_paths == ["/files/document.txt"]

    async def test_downloads_file_for_m365_copilot_channel(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://attachments.example/document.txt",
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="document.txt",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.m365_copilot,
            attachments=[attachment],
        )

        assert len(files) == 1
        assert download_server.requested_paths == ["/files/document.txt"]

    async def test_ignores_attachments_from_non_m365_channel(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://attachments.example/document.txt",
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="document.txt",
        )
        downloader = M365AttachmentDownloader(
            connections=agent_environment.connections,
        )

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloader,
            channel_id=Channels.webchat,
            attachments=[attachment],
        )

        assert files == []
        assert download_server.requested_paths == []

    async def test_composes_with_generic_downloader_without_duplicate_files(
        self,
        agent_client: AgentClient,
        agent_environment: AgentEnvironment,
        download_server: DownloadServer,
    ):
        attachment = Attachment(
            content_type="text/plain",
            content_url="https://attachments.example/document.txt",
            content={
                "downloadUrl": download_server.url("/files/document.txt"),
            },
            name="document.txt",
        )
        downloaders = [
            AttachmentDownloader(),
            M365AttachmentDownloader(
                connections=agent_environment.connections,
            ),
        ]

        files = await download_attachments(
            agent_client,
            agent_environment,
            downloaders,
            channel_id=Channels.ms_teams,
            attachments=[attachment],
        )

        assert len(files) == 1
        assert files[0]["filename"] == "document.txt"
        assert download_server.requested_paths == ["/files/document.txt"]
