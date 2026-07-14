# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Backend utilities for the fluent API.

This module provides low-level building blocks for the fluent assertion
and selection system, including predicate evaluation, transforms, and
quantifier functions.
"""

from .describe import Describe
from .transform import (
    DictionaryTransform,
    ModelTransform,
)
from .model_predicate import (
    ModelPredicate,
    ModelPredicateResult,
)
from .quantifier import (
    Quantifier,
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)
from .utils import (
    deep_update,
    expand,
    set_defaults,
    flatten,
)
from .types import Unset

__all__ = [
    "Describe",
    "DictionaryTransform",
    "ModelPredicate",
    "Quantifier",
    "for_all",
    "for_any",
    "for_none",
    "for_one",
    "for_n",
    "deep_update",
    "expand",
    "set_defaults",
    "flatten",
    "ModelTransform",
    "ModelPredicateResult",
    "Unset",
]