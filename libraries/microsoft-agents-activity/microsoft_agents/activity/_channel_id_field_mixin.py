# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging
from typing import Optional, Any

from pydantic import (
    ModelWrapValidatorHandler,
    SerializerFunctionWrapHandler,
    computed_field,
    model_validator,
    model_serializer,
)

from .channel_id import ChannelId

logger = logging.getLogger(__name__)


# can be generalized in the future, if needed
class _ChannelIdFieldMixin:
    """A mixin to add a computed field channel_id of type ChannelId to a Pydantic model."""

    _channel_id: Optional[ChannelId] = None

    # required to define the setter below
    @computed_field(return_type=Optional[ChannelId], alias="channelId")
    @property
    def channel_id(self) -> Optional[ChannelId]:
        """Gets the _channel_id field"""
        return self._channel_id

    # necessary for backward compatibility
    # previously, channel_id was directly assigned with strings
    @channel_id.setter
    def channel_id(self, value: Any):
        """Sets the channel_id after validating it as a ChannelId model."""
        if isinstance(value, ChannelId):
            self._channel_id = value
        elif isinstance(value, str):
            self._channel_id = ChannelId(value)
        else:
            raise ValueError(
                f"Invalid type for channel_id: {type(value)}. "
                "Expected ChannelId or str."
            )

    def _set_validated_channel_id(self, data: Any) -> None:
        """Sets the channel_id after validating it as a ChannelId model."""
        if "channelId" in data:
            self.channel_id = data["channelId"]
        elif "channel_id" in data:
            self.channel_id = data["channel_id"]

    @model_validator(mode="wrap")
    @classmethod
    def _validate_channel_id(
        cls, data: Any, handler: ModelWrapValidatorHandler
    ) -> _ChannelIdFieldMixin:
        """Validate the _channel_id field after model initialization.

        :return: The model instance itself.
        """
        try:
            model = handler(data)
            model._set_validated_channel_id(data)
            return model
        except Exception:
            logging.error("Model %s failed to validate with data %s", cls, data)
            raise

    def _remove_serialized_unset_channel_id(
        self, serialized: dict[str, object]
    ) -> None:
        """Remove the _channel_id field if it is not set."""
        if not self._channel_id:
            if "channelId" in serialized:
                del serialized["channelId"]
            elif "channel_id" in serialized:
                del serialized["channel_id"]

    @model_serializer(mode="wrap")
    def _serialize_channel_id(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        """Serialize the model using Pydantic's standard serialization.

        :param handler: The serialization handler provided by Pydantic.
        :return: A dictionary representing the serialized model.
        """
        serialized = handler(self)
        if self:  # serialization can be called with None
            self._remove_serialized_unset_channel_id(serialized)
        return serialized
