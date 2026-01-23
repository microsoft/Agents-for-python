# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import functools
from copy import deepcopy
from typing import Generic, TypeVar, cast, T

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
    """A template for creating BaseModel instances with default values."""

    def __init__(self, model_class: Type[T], defaults: T | dict | None = None, **kwargs) -> None:
        """Initialize the ModelTemplate with default values.
        
        :param defaults: A dictionary or BaseModel containing default values.
        :param kwargs: Additional default values as keyword arguments.
        """
        
        self._model_class: Type[T] = model_class

        defaults = defaults or {}
        normalized_defaults = normalize_model_data(defaults)

        self._defaults: dict = {}
        set_defaults(self._defaults, normalized_defaults, **kwargs)

    def create(self, original: T | dict | None = None) -> T:
        """Create a new BaseModel instance based on the template.
        
        :param original: An optional BaseModel or dictionary to override default values.
        :return: A new BaseModel instance.
        """
        if original is None:
            original = {}
        data = normalize_model_data(original)
        set_defaults(data, self._defaults)
        return self._model_class.model_validate(data)
    
    def with_defaults(self, defaults: dict | None = None, **kwargs) -> ModelTemplate[T]:
        """Create a new ModelTemplate with additional default values.
        
        :param defaults: An optional dictionary of default values.
        :param kwargs: Additional default values as keyword arguments.
        :return: A new ModelTemplate instance.
        """
        new_template = deepcopy(self._defaults)
        set_defaults(new_template, defaults, **kwargs)
        return ModelTemplate[T](self._model_class, new_template)
    
    def with_updates(self, updates: dict | None = None, **kwargs) -> ModelTemplate[T]:
        """Create a new ModelTemplate with updated default values.

        :param updates: An optional dictionary of values to update.
        :param kwargs: Additional values to update as keyword arguments.
        :return: A new ModelTemplate instance.
        """
        new_template = deepcopy(self._defaults)
        deep_update(new_template, updates, **kwargs)
        return ModelTemplate[T](self._model_class, new_template)
    
    def __eq__(self, other: object) -> bool:
        """Check equality between two ModelTemplate instances."""
        if not isinstance(other, ModelTemplate):
            return False
        return self._defaults == other._defaults and \
            self._model_class == other._model_class
    
ActivityTemplate = functools.partial(ModelTemplate, Activity)