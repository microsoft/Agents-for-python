# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from a2a.types import Message, Part, Role, TaskState
from google.protobuf.json_format import ParseDict
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Value

from microsoft_agents.activity import (
    ActivityTypes,
    Channels,
    DeliveryModes,
    RoleTypes,
)
from microsoft_agents.hosting.a2a.activity import A2AActivity


def _message(*parts: Part, task_id: str = "task-1") -> Message:
    return Message(
        message_id="message-1",
        context_id="context-1",
        task_id=task_id,
        role=Role.ROLE_USER,
        parts=list(parts),
    )


def test_from_message_requires_task_id():
    message = _message(Part(text="hello"), task_id="")

    with pytest.raises(ValueError, match="Task ID is required"):
        A2AActivity.from_message("request-1", None, message)


def test_from_message_maps_message_properties():
    message = _message(Part(text="hello"))

    activity = A2AActivity.from_message("request-1", None, message)

    assert activity.type == ActivityTypes.message
    assert activity.channel_id == Channels.a2a
    assert activity.request_id == "request-1"
    assert activity.text == "hello"
    assert activity.conversation.id == "task-1"
    assert activity.delivery_mode == DeliveryModes.stream
    assert activity.from_property.role == RoleTypes.user
    assert activity.recipient.role == RoleTypes.agent
    assert activity.channel_data is message


def test_from_message_uses_explicit_task_id_and_populates_missing_context_id():
    message = _message(Part(text="hello"), task_id="")
    message.context_id = ""

    activity = A2AActivity.from_message("request-1", "explicit-task", message)

    assert activity.conversation.id == "explicit-task"
    assert message.task_id == "explicit-task"
    assert message.context_id


def test_from_message_maps_all_supported_part_types():
    message = _message(
        Part(text="hello "),
        Part(text="world"),
        Part(
            url="https://example.com/image.png",
            media_type="image/png",
            filename="image.png",
        ),
        Part(
            raw=b"file contents",
            media_type="application/octet-stream",
            filename="data.bin",
        ),
        Part(
            data=ParseDict({"answer": 42}, Value()),
            media_type="application/json",
            filename="result.json",
        ),
    )

    activity = A2AActivity.from_message("request-1", None, message)

    assert activity.text == "hello world"
    assert activity.delivery_mode == DeliveryModes.stream
    assert len(activity.attachments) == 3

    url_attachment, raw_attachment, data_attachment = activity.attachments
    assert url_attachment.content_url == "https://example.com/image.png"
    assert url_attachment.content_type == "image/png"
    assert url_attachment.name == "image.png"
    assert raw_attachment.content == b"file contents"
    assert raw_attachment.content_type == "application/octet-stream"
    assert raw_attachment.name == "data.bin"
    assert data_attachment.content == {"answer": 42.0}
    assert data_attachment.content_type == "application/json"
    assert data_attachment.name == "result.json"


def test_supported_parts_round_trip_through_activity_artifact():
    message = _message(
        Part(
            url="https://example.com/image.png",
            media_type="image/png",
            filename="image.png",
        ),
        Part(
            raw=b"file contents",
            media_type="application/octet-stream",
            filename="data.bin",
        ),
        Part(
            data=ParseDict({"answer": 42}, Value()),
            media_type="application/json",
            filename="result.json",
        ),
    )

    activity = A2AActivity.from_message("request-1", None, message)
    artifact = activity.to_artifact("artifact-1")

    assert artifact.parts[0].url == "https://example.com/image.png"
    assert artifact.parts[0].media_type == "image/png"
    assert artifact.parts[1].raw == b"file contents"
    assert artifact.parts[1].media_type == "application/octet-stream"
    assert MessageToDict(artifact.parts[2].data) == {"answer": 42.0}
    assert artifact.parts[2].media_type == "application/json"
    assert artifact.parts[2].filename == "result.json"


def test_empty_text_and_raw_parts_preserve_their_content_kind():
    message = _message(
        Part(text=""),
        Part(
            raw=b"",
            media_type="application/octet-stream",
            filename="empty.bin",
        ),
    )

    activity = A2AActivity.from_message("request-1", None, message)
    artifact = activity.to_artifact("artifact-1")

    assert activity.text == ""
    assert activity.attachments[0].content == b""
    assert artifact.parts[0].WhichOneof("content") == "text"
    assert artifact.parts[0].text == ""
    assert artifact.parts[1].WhichOneof("content") == "raw"
    assert artifact.parts[1].raw == b""


def test_to_message_and_artifact_delegate_activity_content():
    activity = A2AActivity(type=ActivityTypes.message, text="result")

    message = activity.to_message("context-1", "task-1")
    artifact = activity.to_artifact("artifact-1")

    assert message.context_id == "context-1"
    assert message.task_id == "task-1"
    assert message.role == Role.ROLE_AGENT
    assert [part.text for part in message.parts] == ["result"]
    assert artifact.artifact_id == "artifact-1"
    assert [part.text for part in artifact.parts] == ["result"]


def test_get_task_state_delegates_to_activity_state():
    activity = A2AActivity(type=ActivityTypes.message)

    assert activity.get_task_state() == TaskState.TASK_STATE_WORKING
