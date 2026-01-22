from copy import deepcopy
from typing import Generic, TypeVar

from pydantic import BaseModel
from microsoft_agents.activity import Activity

from .data import (
    deep_model_copy,
    normalize_model_data,
    update_with_defaults,
)

T = TypeVar("T", bound=BaseModel)

def normalize_model_data(source: BaseModel | dict) -> dict:
    """Normalize AgentsModel data to a dictionary format."""

    if isinstance(source, BaseModel):
        return source.model_dump(exclude_unset=True, mode="json")
    return source

def deep_model_copy(source: BaseModel | dict) -> dict:
    """Create a deep copy of AgentsModel data in dictionary format."""

    normalized_data = normalize_model_data(source)
    deep_copied_data = deepcopy(normalized_data)

    if isinstance(source, BaseModel):
        return type(source).model_validate(deep_copied_data)
    return deep_copied_data

class ModelTemplate(Generic[T]):

    def __init__(self, defaults: T | dict) -> None:
        self._defaults = normalize_model_data(defaults)

    def populate(self, original: T | dict) -> T:

        original_norm = normalize_model_data(deep_model_copy(original))

        populated_dict = update_with_defaults(original_norm, self._defaults)
        return type(T).model_validate(populated_dict)
    
ActivityTemplate = ModelTemplate[Activity]

def populate_model(original: T | dict, defaults: T | dict) -> T:
    template = ModelTemplate[T](defaults)
    return template.populate(original)

populate_activity = populate_model[Activity]