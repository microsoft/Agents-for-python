# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Fluent API for filtering, selecting, and asserting on model collections.

This module provides a fluent interface for working with collections of
models (such as Activities or Exchanges), enabling expressive test assertions
and data filtering.

Key classes:
    - Expect: Make assertions on collections with quantifiers (all, any, none).
    - Select: Filter and transform collections fluently.
    - ActivityTemplate: Create Activity instances with default values.
    - ModelTemplate: Generic template for creating model instances.
"""

from .backend import (
    DictionaryTransform,
    ModelTransform,
    Describe,
    ModelPredicateResult,
    ModelPredicate,
    Quantifier,
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
    flatten,
    expand,
    deep_update,
    set_defaults,
    Unset,
)

from .expect import Expect
from .select import Select
from .model_template import ModelTemplate, ActivityTemplate
from .utils import normalize_model_data

__all__ = [
    "DictionaryTransform",
    "ModelTransform",
    "Describe",
    "ModelPredicateResult",
    "ModelPredicate",
    "Quantifier",
    "for_all",
    "for_any",
    "for_none",
    "for_one",
    "for_n",
    "ActivityTemplate",
    "Expect",
    "Select",
    "ModelTemplate",
    "flatten",
    "expand",
    "deep_update",
    "set_defaults",
    "normalize_model_data",
    "Unset",
]