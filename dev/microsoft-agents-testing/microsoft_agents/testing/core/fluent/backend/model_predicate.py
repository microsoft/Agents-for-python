# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""ModelPredicate - Evaluate predicates against model collections.

Provides the core predicate evaluation logic used by Expect and Select
to match items against specified criteria.
"""

from __future__ import annotations

from typing import Callable, cast
from dataclasses import dataclass

from pydantic import BaseModel

from .transform import DictionaryTransform, ModelTransform
from .quantifier import (
    Quantifier,
    for_all,
)

@dataclass
class ModelPredicateResult:
    """Result of evaluating a predicate against a list of models.
    
    Contains the source data, the transformation applied, and per-item
    boolean results indicating which items matched the predicate.
    
    Attributes:
        source: The original list of dictionaries that were evaluated.
        dict_transform: The transformation mapping that was applied.
        result_bools: Boolean results per item (True = matched).
        result_dicts: Detailed results per item showing which fields matched.
    """

    source: list[dict]
    dict_transform: dict
    result_bools: list[bool]
    result_dicts: list[dict]

    def __init__(self, source: list[dict] | list[BaseModel], dict_transform: dict, result_dicts: list[dict]) -> None:
        if isinstance(source, list) and source and isinstance(source[0], BaseModel):
            source = cast(list[BaseModel], source)
            self.source = cast(list[dict], [s.model_dump(exclude_unset=True, mode="json") for s in source])
        else:
            self.source = cast(list[dict], source)
        self.dict_transform = dict_transform
        self.result_dicts = result_dicts
        self.result_bools = [ self._truthy(d) for d in self.result_dicts ]

    def _truthy(self, result: dict | list) -> bool:

        res: list[bool] = []

        if isinstance(result, dict):
            iterable = result.values()
        else:
            iterable = result

        for val in iterable:
            if isinstance(val, (dict, list)):
                res.append(self._truthy(val))
            else:
                res.append(bool(val))

        return all(res)

class ModelPredicate:
    """Evaluates predicates against models to produce boolean results.
    
    Wraps a DictionaryTransform to evaluate it against one or more models,
    producing a ModelPredicateResult with per-item match information.
    """

    def __init__(self, dict_transform: DictionaryTransform) -> None:
        self._dt = dict_transform
        self._transform = ModelTransform(dict_transform)
    
    def eval(self, source:  dict | BaseModel | list[dict] | list[BaseModel]) -> ModelPredicateResult:
        if not isinstance(source, list):
            source = cast(list[dict] | list[BaseModel], [source])
        res = self._transform.eval(source)
        return ModelPredicateResult(source, self._dt.map, res)
        
    @staticmethod
    def from_args(arg: dict | Callable | None | ModelPredicate, **kwargs) -> ModelPredicate:
        if isinstance(arg, ModelPredicate):
            return arg
        
        return ModelPredicate(
            DictionaryTransform.from_args(arg, **kwargs)
        )