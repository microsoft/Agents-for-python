# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import SimpleNamespace

import pytest
from a2a.types import Message, Role, TaskState
from google.protobuf.json_format import MessageToDict

from microsoft_agents.activity import (
    Activity,
    Attachment,
    Entity,
    InputHints,
    StreamInfo,
)
from microsoft_agents.hosting.a2a.activity import utils


def test_activity_to_artifact_maps_text_value_and_attachments():
    activity = Activity(
        type="message",
        text="hello",
        value={"result": "ok"},
        attachments=[
            Attachment(
                content_type="image/png",
                content_url="https://example.com/image.png",
                name="image.png",
            ),
            Attachment(
                content_type="application/json",
                content={"count": 2},
                name="result.json",
            ),
        ],
    )

    artifact = utils.activity_to_artifact(activity, artifact_id="artifact-1")

    assert artifact.artifact_id == "artifact-1"
    assert artifact.parts[0].text == "hello"
    assert MessageToDict(artifact.parts[1].data)["result"] == "ok"
    assert artifact.parts[2].url == "https://example.com/image.png"
    assert artifact.parts[2].media_type == "image/png"
    assert artifact.parts[2].filename == "image.png"
    assert MessageToDict(artifact.parts[3].data)["count"] == 2
    assert artifact.parts[3].media_type == "application/json"


def test_activity_to_artifact_adds_entities_and_excludes_stream_info():
    activity = Activity(
        type="message",
        entities=[
            Entity(type="citation"),
            StreamInfo(stream_id="stream-1", stream_sequence=1),
        ],
    )

    artifact = utils.activity_to_artifact(activity)

    assert len(artifact.parts) == 1
    assert MessageToDict(artifact.parts[0].data)["type"] == "citation"
    assert artifact.parts[0].metadata["mimeType"] == "application/json"
    assert artifact.parts[0].metadata["type"] == "object"
    assert artifact.parts[0].metadata["schema"]["title"] == "Entity"
    assert artifact.parts[0].metadata["schema"]["required"] == ["type"]


def test_activity_to_artifact_can_exclude_entities():
    activity = Activity(type="message", entities=[Entity(type="citation")])

    artifact = utils.activity_to_artifact(activity, include_entities=False)

    assert list(artifact.parts) == []


def test_activity_to_artifact_rejects_unsupported_attachment_content():
    activity = Activity(
        type="message",
        attachments=[
            Attachment(
                content_type="text/plain",
                content="plain text",
            )
        ],
    )

    with pytest.raises(RuntimeError, match="Unsupported attachment content type"):
        utils.activity_to_artifact(activity)


def test_create_artifact_from_data_returns_none_for_none():
    assert utils.create_artifact_from_data(None) is None


def test_create_artifact_from_data_populates_artifact():
    artifact = utils.create_artifact_from_data(
        {"answer": 42},
        name="result",
        description="The result",
        media_type="application/json",
        artifact_id="artifact-1",
    )

    assert artifact.artifact_id == "artifact-1"
    assert artifact.name == "result"
    assert artifact.description == "The result"
    assert MessageToDict(artifact.parts[0].data)["answer"] == 42
    assert artifact.parts[0].metadata["mimeType"] == "application/json"
    assert artifact.parts[0].metadata["type"] == "object"
    assert artifact.parts[0].metadata["schema"] == {
        "additionalProperties": True,
        "type": "object",
    }


def test_get_a2a_metadata_rejects_none():
    with pytest.raises(ValueError, match="Data cannot be None"):
        utils._get_a2a_metadata(None)


def test_get_a2a_metadata_reuses_cached_schema_for_same_type():
    utils._try_get_json_schema.cache_clear()

    first = utils._get_a2a_metadata(Entity(type="citation"))
    second = utils._get_a2a_metadata(Entity(type="mention"))

    assert first["schema"] == second["schema"]
    assert utils._try_get_json_schema.cache_info().misses == 1
    assert utils._try_get_json_schema.cache_info().hits == 1


def test_create_message_without_activity_has_agent_role_and_no_parts():
    message = utils.create_message("context-1", "task-1", None)

    assert message.context_id == "context-1"
    assert message.task_id == "task-1"
    assert message.message_id
    assert message.role == Role.ROLE_AGENT
    assert list(message.parts) == []


@pytest.mark.parametrize(
    ("activity", "expected"),
    [
        (Activity(type="message"), False),
        (Activity(type="message", text="hello"), True),
        (
            Activity(
                type="message",
                attachments=[Attachment(content_type="text/plain", content="hello")],
            ),
            True,
        ),
    ],
)
def test_has_message_content(activity, expected):
    assert utils.has_message_content(activity) is expected


def test_get_task_state_maps_input_hint():
    assert (
        utils.get_task_state(
            Activity(type="message", input_hint=InputHints.expecting_input)
        )
        == TaskState.TASK_STATE_INPUT_REQUIRED
    )
    assert (
        utils.get_task_state(Activity(type="message"))
        == TaskState.TASK_STATE_WORKING
    )


def test_get_incoming_message_returns_a2a_message():
    message = Message(message_id="message-1", role=Role.ROLE_USER)
    context = SimpleNamespace(
        activity=Activity(type="message", channel_data=message)
    )

    assert utils.get_incoming_message(context) is message


def test_get_incoming_message_rejects_other_channel_data():
    context = SimpleNamespace(
        activity=Activity(type="message", channel_data={"message": "hello"})
    )

    with pytest.raises(TypeError, match="Expected channel_data"):
        utils.get_incoming_message(context)
