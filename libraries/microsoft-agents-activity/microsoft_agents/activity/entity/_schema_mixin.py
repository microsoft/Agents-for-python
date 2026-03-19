# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Self
from pydantic import (
    model_serializer,
    model_validator,
    ModelWrapValidatorHandler,
    SerializerFunctionWrapHandler,
    BaseModel,
)


def validate_schema_model(cls, data: Any, handler: ModelWrapValidatorHandler):
    model = handler(data)
    if isinstance(data, dict):
        if "@type" in data:
            setattr(model, "at_type", data["@type"])
        if "@context" in data:
            setattr(model, "at_context", data["@context"])
    return model


def serialize_schema_model(
    self, handler: SerializerFunctionWrapHandler
) -> dict[str, object]:
    serialized = handler(self)
    if hasattr(self, "at_type"):
        serialized["@type"] = getattr(self, "at_type")
    if hasattr(self, "at_context"):
        serialized["@context"] = getattr(self, "at_context")
    return serialized


class _SchemaMixin(BaseModel):
    """Mixin class to force inclusion of @property fields when serializing."""

    @model_validator(mode="wrap")
    @classmethod
    def validate_model(
        cls, data: Any, handler: ModelWrapValidatorHandler[Self]
    ) -> Self:
        return validate_schema_model(cls, data, handler)

    @model_serializer(mode="wrap")
    def serialize_model(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        return serialize_schema_model(self, handler)
