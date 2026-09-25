# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

from microsoft_agents.activity import Activity, ActivityTypes, Attachment
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.hosting.core.app.input_file import InputFileDownloader
from microsoft_agents.hosting.testing import (
    AgentClient,
    AgentEnvironment,
    AiohttpScenario,
)


def _configure_agent(env: AgentEnvironment) -> None:
    @env.agent_application.message("Download the attached files.")
    async def report_downloaded_files(context: TurnContext, state: TurnState) -> None:
        files = [
            {
                "content": file.content.decode("utf-8"),
                "content_type": file.content_type,
                "content_url": file.content_url,
                "filename": file.filename,
            }
            for file in state.temp.input_files
        ]
        await context.send_activity(json.dumps(files))


DOWNLOADER_SCENARIO = AiohttpScenario.create(
    _configure_agent,
    use_jwt_middleware=False,
)


async def download_attachments(
    agent_client: AgentClient,
    agent_environment: AgentEnvironment,
    downloaders: InputFileDownloader | list[InputFileDownloader],
    *,
    channel_id: str,
    attachments: list[Attachment],
) -> list[dict]:
    if isinstance(downloaders, InputFileDownloader):
        downloaders = [downloaders]
    agent_environment.agent_application.options.file_downloaders = downloaders
    activity = Activity(
        type="message",
        text="Download the attached files.",
        channel_id=channel_id,
        attachments=attachments,
    )

    exchanges = await agent_client.ex_send_expect_replies(activity)

    assert len(exchanges) == 1
    assert exchanges[0].error is None
    replies = [
        response
        for response in exchanges[0].responses
        if response.type == ActivityTypes.message
    ]
    assert len(replies) == 1, (
        f"Expected one agent reply, got {len(replies)} "
        f"(status={exchanges[0].status_code}, body={exchanges[0].body!r})"
    )
    assert replies[0].text is not None
    return json.loads(replies[0].text)
