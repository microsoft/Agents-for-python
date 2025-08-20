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
