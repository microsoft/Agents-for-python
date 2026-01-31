# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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

    result_bools: list[bool]
    result_dicts: list[dict]
    
    def __init__(self, result_dicts: list[dict]) -> None:
        self.result_dicts = result_dicts
        self.result_bools = [ self._truthy(d) for d in self.result_dicts ]

    def _truthy(self, result: dict) -> bool:

        res: bool = []

        for key, val in result.items():
            if isinstance(val, (dict, list)):
                res.append(self._truthy(val))
            else:
                res.append(bool(val))

        return all(res)

class ModelPredicate:

    def __init__(self, dict_transform: DictionaryTransform) -> None:
        self._transform = ModelTransform(dict_transform)
    
    def eval(self, source:  dict | BaseModel | list[dict] | list[BaseModel]) -> ModelPredicateResult:
        if not isinstance(source, list):
            source = cast(list[dict] | list[BaseModel], [source])
        mpr = self._transform.eval(source)
        return ModelPredicateResult(mpr)
        
    @staticmethod
    def from_args(arg: dict | Callable | None | ModelPredicate, **kwargs) -> ModelPredicate:
        if isinstance(arg, ModelPredicate):
            return arg
        
        return ModelPredicate(
            DictionaryTransform.from_args(arg, **kwargs)
        )