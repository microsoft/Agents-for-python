# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC
from typing import Any, Callable

from .agents_model import AgentsModel


class ModelFieldHelper(ABC):
    """Base class for model field processing prior to initialization of an AgentsModel"""

    def process(self, key: str) -> dict[str, Any]:
        """Takes the key in the destination object and returns a dictionary of new fields to add"""
        raise NotImplementedError()


class SkipIf(ModelFieldHelper):
    """Skip if the value meets the given condition."""

    def __init__(self, value, skip_condition: Callable[[Any], bool]):
        self.value = value
        self._skip_condition = skip_condition

    def process(self, key: str) -> dict[str, Any]:
        if self._skip_condition(self.value):
            return {}
        return {key: self.value}


class SkipNone(SkipIf):
    """Skip if the value is None."""

    def __init__(self, value):
        super().__init__(value, lambda v: v is None)


def pick_model_dict(**kwargs):
    """Processes a list of keyword arguments, using ModelFieldHelper subclasses to determine which fields to include in the final model.

    This function is useful for dynamically constructing models based on varying input data.

    Usage:
        activity_dict = pick_model_dict(type="message", id="123", text=SkipNone(text_variable))
        activity = Activity.model_validate(activity_dict)
    """

    model_dict = {}
    for key, value in kwargs.items():
        if not isinstance(value, ModelFieldHelper):
            model_dict[key] = value
        else:
            model_dict.update(value.process(key))

    return model_dict


def pick_model(model_class: type[AgentsModel], **kwargs) -> AgentsModel:
    """Picks model fields from the given keyword arguments.

    Usage:
        activity = pick_model(Activity, type="message", id="123", text=SkipNone(text_variable))
    """
    return model_class(**pick_model_dict(**kwargs))
