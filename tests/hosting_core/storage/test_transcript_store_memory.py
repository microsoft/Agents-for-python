# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timezone
import pytest
from microsoft_agents.hosting.core.storage.transcript_memory_store import (
    TranscriptMemoryStore,
)
from microsoft_agents.activity import Activity, ConversationAccount


@pytest.mark.asyncio
async def test_get_transcript_empty():
    store = TranscriptMemoryStore()
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert transcript == []
    assert continuationToken is None


@pytest.mark.asyncio
async def test_log_activity_add_one_activity():
    store = TranscriptMemoryStore()
    activity = Activity.create_message_activity()
    activity.text = "Activity 1"
    activity.channel_id = "Channel 1"
    activity.conversation = ConversationAccount(id="Conversation 1")

    # Add one activity and make sure it's there and comes back
    await store.log_activity(activity)

    # Ask for the activity we just added
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 1
    assert transcript[0].channel_id == activity.channel_id
    assert transcript[0].conversation.id == activity.conversation.id
    assert transcript[0].text == activity.text
    assert continuationToken is None

    # Ask for a channel that doesn't exist and make sure we get nothing
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Invalid", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert transcript == []
    assert continuationToken is None

    # Ask for a ConversationID that doesn't exist and make sure we get nothing
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "INVALID"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert transcript == []
    assert continuationToken is None


@pytest.mark.asyncio
async def test_log_activity_add_two_activity_same_conversation():
    store = TranscriptMemoryStore()
    activity1 = Activity.create_message_activity()
    activity1.text = "Activity 1"
    activity1.channel_id = "Channel 1"
    activity1.conversation = ConversationAccount(id="Conversation 1")

    activity2 = Activity.create_message_activity()
    activity2.text = "Activity 2"
    activity2.channel_id = "Channel 1"
    activity2.conversation = ConversationAccount(id="Conversation 1")

    await store.log_activity(activity1)
    await store.log_activity(activity2)

    # Ask for the activity we just added
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 2
    assert transcript[0].channel_id == activity1.channel_id
    assert transcript[0].conversation.id == activity1.conversation.id
    assert transcript[0].text == activity1.text

    assert transcript[1].channel_id == activity2.channel_id
    assert transcript[1].conversation.id == activity2.conversation.id
    assert transcript[1].text == activity2.text

    assert continuationToken is None


@pytest.mark.asyncio
async def test_log_activity_add_two_activity_same_conversation():
    store = TranscriptMemoryStore()
    activity1 = Activity.create_message_activity()
    activity1.text = "Activity 1"
    activity1.channel_id = "Channel 1"
    activity1.conversation = ConversationAccount(id="Conversation 1")
    activity1.timestamp = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    activity2 = Activity.create_message_activity()
    activity2.text = "Activity 2"
    activity2.channel_id = "Channel 1"
    activity2.conversation = ConversationAccount(id="Conversation 1")
    activity2.timestamp = datetime(2010, 1, 1, 12, 0, 1, tzinfo=timezone.utc)

    activity3 = Activity.create_message_activity()
    activity3.text = "Activity 2"
    activity3.channel_id = "Channel 1"
    activity3.conversation = ConversationAccount(id="Conversation 1")
    activity3.timestamp = datetime(2020, 1, 1, 12, 0, 1, tzinfo=timezone.utc)

    await store.log_activity(activity1)  # 2000
    await store.log_activity(activity2)  # 2010
    await store.log_activity(activity3)  # 2020

    # Ask for the activities we just added
    date1 = datetime(1999, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    date2 = datetime(2009, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    date3 = datetime(2019, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # ask for everything after 1999. Should get all 3 activities
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1", None, date1
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 3

    # ask for everything after 2009. Should get 2 activities - the 2010 and 2020 activities
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1", None, date2
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 2

    # ask for everything after 2019. Should only get the 2020 activity
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1", None, date3
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 1


@pytest.mark.asyncio
async def test_log_activity_add_two_activity_two_conversation():
    store = TranscriptMemoryStore()
    activity1 = Activity.create_message_activity()
    activity1.text = "Activity 1 Channel 1 Conversation 1"
    activity1.channel_id = "Channel 1"
    activity1.conversation = ConversationAccount(id="Conversation 1")

    activity2 = Activity.create_message_activity()
    activity2.text = "Activity 1 Channel 1 Conversation 2"
    activity2.channel_id = "Channel 1"
    activity2.conversation = ConversationAccount(id="Conversation 2")

    await store.log_activity(activity1)
    await store.log_activity(activity2)

    # Ask for the activity we just added
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 1
    assert transcript[0].channel_id == activity1.channel_id
    assert transcript[0].conversation.id == activity1.conversation.id
    assert transcript[0].text == activity1.text
    assert continuationToken is None

    # Now grab Conversation 2
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 2"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 1
    assert transcript[0].channel_id == activity2.channel_id
    assert transcript[0].conversation.id == activity2.conversation.id
    assert transcript[0].text == activity2.text
    assert continuationToken is None


@pytest.mark.asyncio
async def test_delete_one_transcript():
    store = TranscriptMemoryStore()
    activity = Activity.create_message_activity()
    activity.text = "Activity 1"
    activity.channel_id = "Channel 1"
    activity.conversation = ConversationAccount(id="Conversation 1")

    # Add one activity and make sure it's there and comes back
    await store.log_activity(activity)

    # Ask for the activity we just added
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]

    assert len(transcript) == 1

    # Now delete the transcript
    await store.delete_transcript("Channel 1", "Conversation 1")
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    assert len(transcript) == 0


@pytest.mark.asyncio
async def test_delete_one_transcript_of_two():
    store = TranscriptMemoryStore()

    activity = Activity.create_message_activity()
    activity.text = "Activity 1"
    activity.channel_id = "Channel 1"
    activity.conversation = ConversationAccount(id="Conversation 1")

    activity2 = Activity.create_message_activity()
    activity2.text = "Activity 2"
    activity2.channel_id = "Channel 2"
    activity2.conversation = ConversationAccount(id="Conversation 1")

    # Add one activity and make sure it's there and comes back
    await store.log_activity(activity)
    await store.log_activity(activity2)

    # We now have two different transcripts. One for Channel 1 Conversation 1 and one for Channel 2 Conversation 1

    # Delete one of the transcripts
    await store.delete_transcript("Channel 1", "Conversation 1")

    # Make sure the one we deleted is gone
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 1", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    assert len(transcript) == 0

    # Make sure the other one is still there
    transcriptAndContinuationToken = await store.get_transcript_activities(
        "Channel 2", "Conversation 1"
    )
    transcript = transcriptAndContinuationToken[0]
    assert len(transcript) == 1


@pytest.mark.asyncio
async def test_list_transcripts():
    store = TranscriptMemoryStore()

    activity = Activity.create_message_activity()
    activity.text = "Activity 1"
    activity.channel_id = "Channel 1"
    activity.conversation = ConversationAccount(id="Conversation 1")

    activity2 = Activity.create_message_activity()
    activity2.text = "Activity 2"
    activity2.channel_id = "Channel 2"
    activity2.conversation = ConversationAccount(id="Conversation 1")

    # Make sure a list on an empty store returns an empty set
    transcriptAndContinuationToken = await store.list_transcripts("Should Be Empty")
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 0
    assert continuationToken is None

    # Add one activity so we can go searching
    await store.log_activity(activity)

    transcriptAndContinuationToken = await store.list_transcripts("Channel 1")
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 1
    assert continuationToken is None

    # Add second activity on a different channel, so now we have 2 transcripts
    await store.log_activity(activity2)

    # Check again for "Transcript 1" which is on channel 1
    transcriptAndContinuationToken = await store.list_transcripts("Channel 1")
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 1
    assert continuationToken is None

    # Check for "Transcript 2" which is on channel 2
    transcriptAndContinuationToken = await store.list_transcripts("Channel 2")
    transcript = transcriptAndContinuationToken[0]
    continuationToken = transcriptAndContinuationToken[1]
    assert len(transcript) == 1
    assert continuationToken is None
