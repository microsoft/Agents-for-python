# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from microsoft_agents.activity import Activity, ActivityEventNames, ActivityTypes
from microsoft_agents.hosting.core.authorization.claims_identity import ClaimsIdentity
from microsoft_agents.hosting.core.middleware_set import TurnContext
from microsoft_agents.hosting.core.storage.transcript_logger import TranscriptLoggerMiddleware
from microsoft_agents.hosting.core.storage.transcript_memory_store import TranscriptMemoryStore
import pytest

from tests._common.testing_objects.adapters.testing_adapter import AgentCallbackHandler, TestingAdapter

@pytest.mark.asyncio
async def test_should_not_log_continue_conversation():
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
    a1.conversation.id = conversation_id # Make sure the conversation ID is set

    await adapter.process_activity(id, a1, callback)
    
    transcriptAndContinuationToken = await transcript_store.get_transcript_activities(
        channelName, conversation_id
    )
            
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 1
    assert transcript[0].channel_id == channelName
    assert transcript[0].conversation.id == conversation_id
    assert transcript[0].text == a1.text
    assert continuationToken is None