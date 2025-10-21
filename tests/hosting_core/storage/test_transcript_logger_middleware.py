# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import os
from microsoft_agents.activity import Activity, ActivityEventNames, ActivityTypes
from microsoft_agents.hosting.core import ClaimsIdentity, TurnContext
from microsoft_agents.hosting.core.storage import (
    ConsoleTranscriptLogger,
    FileTranscriptLogger,
    TranscriptLoggerMiddleware,
)
from microsoft_agents.hosting.core.storage import (
    TranscriptMemoryStore,
)
import pytest

from tests._common.testing_objects.adapters.testing_adapter import (
    AgentCallbackHandler,
    TestingAdapter,
)


@pytest.mark.asyncio
async def test_should_round_trip_via_middleware():
    transcript_store = TranscriptMemoryStore()
    conversation_id = "id.1"
    transcript_middleware = TranscriptLoggerMiddleware(transcript_store)
    channelName = "Channel1"

    adapter = TestingAdapter(channelName)
    adapter.use(transcript_middleware)
    id = ClaimsIdentity({}, True)

    async def callback(tc):
        print("process callback")

    a1 = adapter.make_activity("some random text")
    a1.conversation.id = conversation_id  # Make sure the conversation ID is set

    await adapter.process_activity(id, a1, callback)

    pagedResult = await transcript_store.get_transcript_activities(
        channelName, conversation_id
    )

    assert len(pagedResult.items) == 1
    assert pagedResult.items[0].channel_id == channelName
    assert pagedResult.items[0].conversation.id == conversation_id
    assert pagedResult.items[0].text == a1.text
    assert pagedResult.continuation_token is None


@pytest.mark.asyncio
async def test_should_write_to_file():
    fileName = "test_transcript.log"

    if os.path.exists(fileName):  # Check if the file exists
        os.remove(fileName)  # Delete the file

    assert not os.path.exists(fileName), "file already exists."

    file_store = FileTranscriptLogger(file_path=fileName)
    conversation_id = "id.1"
    transcript_middleware = TranscriptLoggerMiddleware(file_store)
    channelName = "Channel1"

    adapter = TestingAdapter(channelName)
    adapter.use(transcript_middleware)
    id = ClaimsIdentity({}, True)

    async def callback(tc):
        print("process callback")

    textInActivity = "some random text"
    a1 = adapter.make_activity(textInActivity)
    a1.conversation.id = conversation_id  # Make sure the conversation ID is set

    # This round-trips out to the File logger which does the actual write
    await adapter.process_activity(id, a1, callback)

    # Check the file was created and has content
    assert os.path.exists(fileName), "file was not created"
    assert os.path.isfile(fileName), "file is not a file."
    assert os.path.getsize(fileName) > 0, "file is empty"


@pytest.mark.asyncio
async def test_should_write_to_console():

    store = ConsoleTranscriptLogger()
    conversation_id = "id.1"
    transcript_middleware = TranscriptLoggerMiddleware(store)
    channelName = "Channel1"

    adapter = TestingAdapter(channelName)
    adapter.use(transcript_middleware)
    id = ClaimsIdentity({}, True)

    async def callback(tc):
        print("process callback")

    textInActivity = "some random text"
    a1 = adapter.make_activity(textInActivity)
    a1.conversation.id = conversation_id  # Make sure the conversation ID is set

    # This round-trips out to the console logger which does the actual write
    await adapter.process_activity(id, a1, callback)

    # check the console by hand.
