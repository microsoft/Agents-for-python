# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from uuid import uuid4 as uuid
from typing import Optional, Any
import logging

from pydantic import (
    Field,
    computed_field,
    model_validator,
    ModelWrapValidatorHandler,
    model_serializer,
    SerializerFunctionWrapHandler,
    ValidationError,
)

from .channel_account import ChannelAccount
from .channel_id import ChannelId
from .conversation_account import ConversationAccount
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString
from .activity_types import ActivityTypes
from .activity_event_names import ActivityEventNames

logger = logging.getLogger(__name__)


class ConversationReference(AgentsModel):
    """An object relating to a particular point in a conversation.

    :param activity_id: (Optional) ID of the activity to refer to
    :type activity_id: str
    :param user: (Optional) User participating in this conversation
    :type user: ~microsoft_agents.activity.ChannelAccount
    :param agent: Agent participating in this conversation
    :type agent: ~microsoft_agents.activity.ChannelAccount
    :param conversation: Conversation reference
    :type conversation: ~microsoft_agents.activity.ConversationAccount
    :param channel_id: Channel ID
    :type channel_id: ~microsoft_agents.activity.ChannelId
    :param locale: A locale name for the contents of the text field.
        The locale name is a combination of an ISO 639 two- or three-letter
        culture code associated with a language and an ISO 3166 two-letter
        subculture code associated with a country or region.
        The locale name can also correspond to a valid BCP-47 language tag.
    :type locale: str
    :param service_url: Service endpoint where operations concerning the
     referenced conversation may be performed
    :type service_url: str
    """

    # optionals here are due to webchat
    activity_id: Optional[NonEmptyString] = None
    user: Optional[ChannelAccount] = None
    agent: ChannelAccount = Field(None, alias="bot")
    conversation: ConversationAccount
    _channel_id: ChannelId = None
    locale: Optional[NonEmptyString] = None
    service_url: NonEmptyString = None

    # required to define the setter below
    @computed_field(return_type=Optional[ChannelId])
    @property
    def channel_id(self):
        """Gets the _channel_id field"""
        return self._channel_id

    # necessary for backward compatibility
    # previously, channel_id was directly assigned with strings
    @channel_id.setter
    def channel_id(self, value: Any):
        """Sets the channel_id after validating it as a ChannelId model."""
        self._channel_id = ChannelId.model_validate(value)

    @model_validator(mode="wrap")
    @classmethod
    def _validate_sub_channel_data(
        cls, data: Any, handler: ModelWrapValidatorHandler[ConversationReference]
    ) -> ConversationReference:
        """Validate the ConversationReference, ensuring consistency between channel_id.sub_channel and productInfo entity.

        :param data: The input data to validate.
        :param handler: The validation handler provided by Pydantic.
        :return: The validated ConversationReference instance.
        """
        try:
            # run Pydantic's standard validation first
            conversation_reference = handler(data)

            if isinstance(data, dict):
                # needed to assign to a computed field
                data_channel_id = data.get("channel_id", data.get("channelId"))
                if data_channel_id:
                    conversation_reference.channel_id = data_channel_id

            return conversation_reference
        except ValidationError:
            logger.error("Validation error for ConversationReference")
            raise

    @model_serializer(mode="wrap")
    def _serialize_sub_channel_data(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        """Serialize the ConversationReference, ensuring consistency between channel_id.sub_channel and productInfo entity.

        :param handler: The serialization handler provided by Pydantic.
        :return: A dictionary representing the serialized ConversationReference.
        """

        # run Pydantic's standard serialization first
        serialized = handler(self)

        if serialized:
            # do not include unset value
            if not self.channel_id:
                if "channelId" in serialized:
                    del serialized["channelId"]
                elif "channel_id" in serialized:
                    del serialized["channel_id"]

        return serialized

    def get_continuation_activity(self) -> "Activity":  # type: ignore
        from .activity import Activity

        return Activity(
            type=ActivityTypes.event,
            name=ActivityEventNames.continue_conversation,
            id=str(uuid()),
            channel_id=self.channel_id,
            service_url=self.service_url,
            conversation=self.conversation,
            recipient=self.agent,
            from_property=self.user,
            relates_to=self,
        )
