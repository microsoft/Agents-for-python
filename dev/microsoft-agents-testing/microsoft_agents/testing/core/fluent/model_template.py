# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from copy import deepcopy
from typing import Generic, TypeVar, cast, Self

from pydantic import BaseModel

from microsoft_agents.activity import Activity

from .backend import (
    deep_update,
    expand,
    set_defaults,
)
from .utils import normalize_model_data

ModelT = TypeVar("ModelT", bound=BaseModel | dict)

class ModelTemplate(Generic[ModelT]):
    """A template for creating BaseModel instances with default values."""

    def __init__(self, model_class: type[ModelT], defaults: ModelT | dict | None = None, **kwargs) -> None:
        """Initialize the ModelTemplate with default values.

        Keys with dots (.) are treated as paths representing nested dictionaries.

        :param model_class: The BaseModel class to create instances of.
        :param defaults: A dictionary or BaseModel containing default values.
        :param kwargs: Additional default values as keyword arguments.
        """
        
        self._model_class: type[ModelT] = model_class

        defaults = defaults or {}
        defaults = normalize_model_data(defaults)

        new_defaults: dict = {}
        set_defaults(new_defaults, defaults, **kwargs)
        self._defaults = expand(new_defaults)

    def create(self, original: BaseModel | dict | None = None) -> ModelT:
        """Create a new BaseModel instance based on the template.
        
        :param original: An optional BaseModel or dictionary to override default values.
        :return: A new BaseModel instance.
        """
        if original is None:
            original = {}
        data = normalize_model_data(original)
        set_defaults(data, self._defaults)
        if issubclass(self._model_class, BaseModel):
            return self._model_class.model_validate(data)
        return cast(ModelT, data)
    
    def with_defaults(self, defaults: dict | None = None, **kwargs) -> ModelTemplate[ModelT]:
        """Create a new ModelTemplate with additional default values.
        
        :param defaults: An optional dictionary of default values.
        :param kwargs: Additional default values as keyword arguments.
        :return: A new ModelTemplate instance.
        """
        new_template = deepcopy(self._defaults)
        set_defaults(new_template, defaults, **kwargs)
        return ModelTemplate[ModelT](self._model_class, new_template)
    
    def with_updates(self, updates: dict | None = None, **kwargs) -> ModelTemplate[ModelT]:
        """Create a new ModelTemplate with updated default values."""
        new_template = deepcopy(self._defaults)
        # Expand the updates first so they merge correctly with nested structure
        expanded_updates = expand(updates or {})
        expanded_kwargs = expand(kwargs)
        deep_update(new_template, expanded_updates)
        deep_update(new_template, expanded_kwargs)
        # Pass already-expanded data, avoid re-expansion
        result = ModelTemplate[ModelT](self._model_class, new_template)
        return result
    
    def __eq__(self, other: object) -> bool:
        """Check equality between two ModelTemplate instances."""
        if not isinstance(other, ModelTemplate):
            return False
        return self._defaults == other._defaults and \
            self._model_class == other._model_class
    

class ActivityTemplate(ModelTemplate[Activity]):
    """A template for creating Activity instances with default values."""
    
    def __init__(self, defaults: Activity | dict | None = None, **kwargs) -> None:
        """Initialize the ActivityTemplate with default values.
        
        :param defaults: A dictionary or Activity containing default values.
        :param kwargs: Additional default values as keyword arguments.
        """
        super().__init__(Activity, defaults, **kwargs)
    
    def with_defaults(self, defaults: dict | None = None, **kwargs) -> ActivityTemplate:
        """Create a new ModelTemplate with additional default values.
        
        :param defaults: An optional dictionary of default values.
        :param kwargs: Additional default values as keyword arguments.
        :return: A new ModelTemplate instance.
        """
        new_template = deepcopy(self._defaults)
        set_defaults(new_template, defaults, **kwargs)
        return ActivityTemplate(new_template)
    
    def with_updates(self, updates: dict | None = None, **kwargs) -> ActivityTemplate:
        """Create a new ModelTemplate with updated default values."""
        new_template = deepcopy(self._defaults)
        # Expand the updates first so they merge correctly with nested structure
        expanded_updates = expand(updates or {})
        expanded_kwargs = expand(kwargs)
        deep_update(new_template, expanded_updates)
        deep_update(new_template, expanded_kwargs)
        # Pass already-expanded data, avoid re-expansion
        return ActivityTemplate(new_template)
