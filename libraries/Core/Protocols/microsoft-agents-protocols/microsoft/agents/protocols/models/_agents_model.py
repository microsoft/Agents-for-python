from pydantic import BaseModel, model_serializer
from pydantic.alias_generators import to_camel


class AgentsModel(BaseModel):
    class Config:
        alias_generator = to_camel
    
    '''
    @model_serializer
    def _serialize(self):
        omit_if_empty = {
            k
            for k, v in self
            if isinstance(v, list) and not v
        }

        return {k: v for k, v in self if k not in omit_if_empty and v is not None}
    '''
