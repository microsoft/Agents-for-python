from abc import ABC
from typing import Any, Callable

from microsoft_agents.activity import (
    AgentsModel,
    Activity,
)
from microsoft_agents._model_utils import (
    ModelFieldHelper,
    SkipIf,
    pick_model_dict,
    pick_model
)

class ModelFieldHelper(ABC):
    def process(self, key: str) -> dict[str, Any]:
        raise NotImplemented()

class SkipIf(ModelFieldHelper, ABC):
    def __init__(self, value, check_condition: Callable[[Any], bool] = None):
        self.value = value
        if check_condition is None:
            self._skip = lambda v: v is None

    def process(self, key: str) -> dict[str, Any]:
        if self._skip(self.value):
            return {}
        return {key: self.value}

class SkipNone(SkipIf):
    def __init__(self, value):
        super().__init__(value)

class SkipFalse(SkipIf):
    def __init__(self, value):
        super().__init__(value, lambda x: not bool(x))

class CloneField(ModelFieldHelper):
    def __init__(self, original, key_in_original=None):
        assert isinstance(original, AgentsModel)
        self.original = original
        self.key_in_original = key_in_original
    
    def process(self, key):

        key_in_original = self.key_in_original or key

        if key_in_original in self.original.model_fields_set:
            return { key: getattr(self.original, key_in_original) }
        else:
            return {}



def model_dict(**kwargs):

    activity_dict = {}
    for key, value in kwargs.items():
        if not isinstance(value, ModelFieldHelper):
            activity_dict[key] = value
        else:
            activity_dict.update(value.process(key))

    return activity_dict

def model(model_class: type[AgentsModel], **kwargs) -> AgentsModel:
    return model_class(**model_dict(**kwargs))
