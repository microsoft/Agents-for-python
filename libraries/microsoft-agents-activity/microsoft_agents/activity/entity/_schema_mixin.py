# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any
from pydantic import model_serializer, SerializerFunctionWrapHandler


class _SchemaMixin:

    at_type: Any

    @model_serializer(mode="wrap")
    def serialize_model(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        serialized = handler(self)
        serialized["@type"] = self.at_type
        if hasattr(self, "@context"):
            serialized["@context"] = getattr(self, "at_context")
        return serialized
