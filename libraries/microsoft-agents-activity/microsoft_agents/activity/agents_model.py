# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AgentsModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    """
    @model_serializer
    def _serialize(self):
        omit_if_empty = {
            k
            for k, v in self
            if isinstance(v, list) and not v
        }

        return {k: v for k, v in self if k not in omit_if_empty and v is not None}
    """

    @classmethod
    def pick_properties(cls, original: AgentsModel, fields_to_copy=None, **kwargs):
        """Picks properties from the original model and returns a new instance (of a possibly different AgentsModel) with those properties.

        This method preserves unset values.

        args:
            original: The original model instance to copy properties from. If None, returns None.
            fields_to_copy: The specific fields to copy. If None, all fields are copied.
            **kwargs: Additional fields to include in the new instance.
        """
        if not original:
            return None

        if fields_to_copy is None:
            fields_to_copy = original.model_fields_set
        else:
            fields_to_copy = original.model_fields_set & set(fields_to_copy)

        dest = {}
        for field in fields_to_copy:
            dest[field] = getattr(original, field)

        dest.update(kwargs)
        return cls.model_validate(dest)
