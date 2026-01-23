from __future__ import annotations

from copy import deepcopy
from typing import Generic, TypeVar, cast

from pydantic import BaseModel
from microsoft_agents.activity import Activity

from .data_utils import (
    expand,
    set_defaults,
    deep_update,
)

T = TypeVar("T", bound=BaseModel)

def normalize_model_data(source: BaseModel | dict) -> dict:
    """Normalize AgentsModel data to a dictionary format.

    Creates a deep copy if the source is a dictionary.

    :param source: The AgentsModel or dictionary to normalize.
    :return: The normalized dictionary.
    """

    if isinstance(source, BaseModel):
        source = cast(dict, source.model_dump(exclude_unset=True, mode="json"))
        return source
    
    return expand(source)

class ModelTemplate(Generic[T]):

    def __init__(self, defaults: T | dict, **kwargs) -> None:
        self._defaults: dict = {}
        set_defaults(self._defaults, defaults, **kwargs)

    def create(self, original: T | dict | None = None) -> T:
        if original is None:
            original = {}
        data = normalize_model_data(original)
        deep_update(data, self._defaults)
        return type(T).model_validate(data)
    
    def with_defaults(self, defaults: dict | None = None, **kwargs) -> ModelTemplate[T]:
        new_template = deepcopy(self._defaults)
        set_defaults(new_template, defaults, **kwargs)
        return ModelTemplate[T](new_template)
    
    def with_updates(self, updates: dict | None = None, **kwargs) -> ModelTemplate[T]:
        new_template = deepcopy(self._defaults)
        deep_update(new_template, updates, **kwargs)
        return ModelTemplate[T](new_template)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelTemplate):
            return False
        return self._defaults == other._defaults
    
ActivityTemplate = ModelTemplate[Activity]