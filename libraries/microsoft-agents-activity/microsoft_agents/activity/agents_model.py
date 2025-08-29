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
        if not original:
            return {}

        if fields_to_copy is None:
            fields_to_copy = set(original.model_fields_set)
        else:
            fields_to_copy = original.model_fields_set & set(fields_to_copy)

        clone_dict = {}
        for field in fields_to_copy:
            if field in kwargs:
                clone_dict[field] = getattr(original, field)
                setattr(self, field, kwargs[field])

        clone_dict.update(kwargs)
        return cls.model_validate(clone_dict)