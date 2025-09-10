from abc import ABC
from typing import Any, Callable

from microsoft_agents.activity import (
    AgentsModel,
    Activity,
)
from microsoft_agents.activity._model_utils import (
    ModelFieldHelper,
    SkipIf,
    pick_model_dict,
    pick_model,
)


class SkipFalse(SkipIf):
    def __init__(self, value):
        super().__init__(value, lambda x: not bool(x))


class SkipEmpty(SkipIf):
    def __init__(self, value):
        super().__init__(value, lambda x: len(x) == 0)


class PickField(ModelFieldHelper):
    def __init__(self, original, key_in_original=None):
        assert isinstance(original, AgentsModel)
        self.original = original
        self.key_in_original = key_in_original

    def process(self, key):

        target_key = self.key_in_original or key

        if target_key in self.original.model_fields_set:
            return {key: getattr(self.original, target_key)}
        else:
            return {}
