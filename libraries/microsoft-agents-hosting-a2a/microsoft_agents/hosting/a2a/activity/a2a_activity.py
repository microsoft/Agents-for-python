# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams-aware :class:`Activity` subclass exposing Teams channel data helpers."""

from __future__ import annotations

from typing import Literal, Mapping
from uuid import uuid4

from a2a.types import (
    Artifact,
    Message,
    Part,
    Task,
    TaskState,
)

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    Channels,
    ChannelId,
    ChannelAccount,
    ConversationAccount,
    DeliveryModes,
    RoleTypes,
    InputHints,
    StreamInfo,
)

_DEFAULT_USER_ID = "unknown"
_ENTITY_TYPE_TEMPLATE = "application/vnd.microsoft.entity.{0}"

_SCHEMAS: dict[str, Mapping] = {}

class A2AActivity(Activity):
    """A2A-aware :class:`Activity` subclass exposing A2A protocol data helpers."""

    @staticmethod
    def activity_from_message(request_id: str, task_id: str | None, message: Message) -> A2AActivity:

        if not task_id and not message.task_id:
            raise ValueError("T")
        
        task_id = task_id or  message.task_id 

        activity = A2AActivity._create_activity(
            task_id,
            message.parts,
            True,
            True
        )

    def create_message(self, context_id: str, task_id: str, activity: Activity, include_entities: bool = True) -> Message:
        artifact = self.create_artifact(include_entities=include_entities)
        return Message(
            task_id=task_id,
            context_id=context_id,
            message_id=str(uuid4()),
            parts=artifact.parts,
            role=RoleTypes.agent,
        )

    def create_artifact(self, artifact_id: str | None = None, include_entities: bool = True) -> Artifact:

        artifact = Artifact(
            artifact_id=artifact_id if artifact_id else str(uuid4()),
        )

        if self.text is not None:
            artifact.parts.append(Part(text=self.text))

        if self.value is not None and isinstance(self.value, dict):
            artifact.parts.append(Part(data=self.value))

        for attachment in self.attachments:
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
                        _SCHEMAS[entity.type] = _to_a2a_metadata(entity, _ENTITY_TYPE_TEMPLATE.format(entity.type))

                    cached_metadata = _SCHEMAS[entity.type]

                    artifact.parts.append(Part(
                        metadata=cached_metadata,
                        data=entity.model_dump(exclude_none=True),
                    ))
                
        return artifact

    @staticmethod
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
            artifact_id=artifact_id if artifact_id else str(uuid4()), # check .NET
            name=name,
            description=description,
            parts=[
                Part(
                    data=data,
                    metadata=_get_a2a_metadata(data, media_type or data.__class__.__name__)
                )
            ]
        )

    def has_message_content(self) -> bool:
        return bool(self.text) or bool(self.attachments)

    def get_task_state(self) -> TaskState:
        if self.input_hint == InputHints.expecting_input:
            return TaskState.TASK_STATE_INPUT_REQUIRED
        return TaskState.TASK_STATE_WORKING

    @staticmethod
    def _create_activity(
        conversation_id: str,
        parts: list[Part],
        is_ingress: bool,
        is_streaming: bool
    ) -> A2AActivity:
        """Create an Activity representing an A2A concept."""

        agent = ChannelAccount(id="assistant", role=RoleTypes.agent)
        user = ChannelAccount(id=_DEFAULT_USER_ID, role=RoleTypes.user)

        activity = A2AActivity(
            type=ActivityTypes.message,
            id=str(uuid4()),
            channel_id=ChannelId(Channels.a2a),
            delivery_mode=DeliveryModes.stream if is_streaming else DeliveryModes.expect_replies,
            conversation=ConversationAccount(id=conversation_id),
            recipient=agent if is_ingress else user,
            from_property=user if is_ingress else agent,
        )

        for part in parts:
            if part.content_case

        return activity