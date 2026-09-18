# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Mapping, cast, Sequence
from uuid import uuid4

from a2a.types import (
    Artifact,
    Part,
    Message,
    TaskState,
)

from microsoft_agents.activity import (
    Activity,
    InputHints,
    RoleTypes,
    StreamInfo,
)
from microsoft_agents.hosting.core import TurnContext

_ENTITY_TYPE_TEMPLATE = "application/vnd.microsoft.entity.{0}"
_SCHEMAS: dict[str, Mapping] = {}


def activity_to_artifact(
    activity: Activity, artifact_id: str | None = None, include_entities: bool = True
) -> Artifact:

    artifact = Artifact(
        artifact_id=artifact_id if artifact_id else str(uuid4()),
    )

    if activity.text is not None:
        artifact.parts.append(Part(text=activity.text))

    if activity.value is not None and isinstance(activity.value, dict):
        artifact.parts.append(Part(data=activity.value))

    for attachment in activity.attachments:
        if attachment.content_url and not isinstance(attachment.content, str):
            continue

        part: Part
        if attachment.content_url:
            part = Part(
                url=attachment.content_url,
                media_type=attachment.content_type,
                filename=attachment.name,
            )
        elif isinstance(attachment.content, dict):
            part = Part(
                data=attachment.content,
                media_type=attachment.content_type,
            )
        else:
            raise RuntimeError("Unsupported attachment content type.")

        artifact.parts.append(part)

    if include_entities:
        for entity in self.entities:
            if not isinstance(entity, StreamInfo):

                if entity.type not in _SCHEMAS:
                    _SCHEMAS[entity.type] = _to_a2a_metadata(
                        entity, _ENTITY_TYPE_TEMPLATE.format(entity.type)
                    )

                cached_metadata = _SCHEMAS[entity.type]

                artifact.parts.append(
                    Part(
                        metadata=cached_metadata,
                        data=entity.model_dump(exclude_none=True),
                    )
                )

    return artifact


def create_artifact_from_data(
    data: dict,
    name: str | None = None,
    description: str | None = None,
    media_type: str | None = None,
    artifact_id: str | None = None,
) -> Artifact | None:
    if data is None:
        return None

    return Artifact(
        artifact_id=artifact_id if artifact_id else str(uuid4()),  # check .NET
        name=name,
        description=description,
        parts=[
            Part(
                data=data,
                metadata=_get_a2a_metadata(data, media_type or data.__class__.__name__),
            )
        ],
    )


def create_message(
    context_id: str,
    task_id: str,
    activity: Activity | None,
    include_entities: bool = True,
) -> Message:

    parts: Sequence[Part] | None

    if not activity:
        parts = None
    else:
        artifact = activity_to_artifact(activity, include_entities=include_entities)
        parts = artifact.parts

    return Message(
        task_id=task_id,
        context_id=context_id,
        message_id=str(uuid4()),
        parts=parts,
        role=RoleTypes.agent,
    )


def has_message_content(activity: Activity) -> bool:
    return bool(activity.text) or bool(activity.attachments)


def get_task_state(self) -> TaskState:
    if self.input_hint == InputHints.expecting_input:
        return TaskState.TASK_STATE_INPUT_REQUIRED
    return TaskState.TASK_STATE_WORKING


def get_incoming_message(context: TurnContext) -> Message:
    data = context.activity.channel_data
    if isinstance(data, Message):
        return cast(Message, data)
    raise TypeError("Expected channel_data to be of type Message")
