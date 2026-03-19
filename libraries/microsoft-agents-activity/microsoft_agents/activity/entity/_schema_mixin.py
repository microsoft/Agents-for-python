# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Self
from pydantic import (
    model_serializer,
    model_validator,
    ModelWrapValidatorHandler,
    SerializerFunctionWrapHandler,
    SerializationInfo,
    BaseModel,
)


def validate_schema_model(data: Any, handler: ModelWrapValidatorHandler):
    """Custom validator to handle the aliases @type, @context, and @id if defined in the destination type."""
    model = handler(data)
    if isinstance(data, dict):
        if "@type" in data:
            setattr(model, "at_type", data["@type"])
        if "@context" in data:
            setattr(model, "at_context", data["@context"])
        if "@id" in data:
            setattr(model, "at_id", data["@id"])
    return model


def serialize_schema_model(
    self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
) -> dict[str, Any]:
    """Custom serializer to convert keys to force inclusion of @type, @context, and @id if defined."""
    serialized = handler(self)
    if info.by_alias:
        if hasattr(self, "at_type"):
            serialized["@type"] = getattr(self, "at_type")
        if hasattr(self, "at_context"):
            serialized["@context"] = getattr(self, "at_context")
        if hasattr(self, "at_id"):
            serialized["@id"] = getattr(self, "at_id")
    return serialized


class _SchemaMixin(BaseModel):
    """Mixin class to force inclusion of @property fields when serializing."""

    @model_validator(mode="wrap")
    @classmethod
    def _validate_model(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        return validate_schema_model(data, handler)

    @model_serializer(mode="wrap")
    def _serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: SerializationInfo
    ) -> dict[str, Any]:
        return serialize_schema_model(self, handler, info)
