# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import inspect
from typing import Any, Callable, overload, TypeVar

from pydantic import BaseModel

from .types import Unset
from .utils import expand, flatten

T = TypeVar("T")

class DictionaryTransform:

    MODEL_PREDICATE_ROOT_CALLABLE_KEY = '__ModelPredicate_root_callable_key__'
    
    def __init__(self, arg: dict | Callable | None, **kwargs) -> None:

        if not isinstance(arg, (dict, Callable)) and arg is not None:
            raise ValueError("Argument must be a dictionary or callable.")

        if isinstance(arg, dict) or arg is None:
            temp = arg or {}
        else:
            temp = {}

        if callable(arg):
            temp[self.MODEL_PREDICATE_ROOT_CALLABLE_KEY] = arg

        flat_root = flatten(temp)
        flat_kwargs = flatten(kwargs)

        combined = {**flat_root, **flat_kwargs}
        for key, val in combined.items():
            if isinstance(val, Callable):
                flat_root[key] = val
            else:
                # TODO, does this capture the right data?
                flat_root[key] = lambda x, _v=val: x == _v

        self._map = flat_root

    @staticmethod
    def _get(actual: dict, key: str) -> Any:
        keys = key.split(".")
        current = actual
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return Unset
            current = current[k]
        return current

    def _invoke(
            self,
            actual: dict,
            key: str,
            func: Callable[..., T],
        ) -> T:

        args = {}
        
        sig = inspect.getfullargspec(func)
        func_args = sig.args

        if "actual" in func_args:
            args["actual"] = self._get(actual, key)
        elif "x" in func_args:
            args["x"] = self._get(actual, key)
            
        return func(**args)
        
    def eval(self, actual: dict) -> dict:        
        result = {}
        for key, func in self._map.items():
            if not callable(func):
                raise RuntimeError(f"Predicate value for key '{key}' is not callable")
            result[key] = self._invoke(actual, key, func)

        return expand(result)

    @staticmethod
    def from_args(arg: dict | DictionaryTransform | Callable | Any, **kwargs) -> DictionaryTransform:
        """Creates a DictionaryTransform from arbitrary arguments.
        
        :param args: Positional arguments to create the predicate from.
        :param kwargs: Keyword arguments to create the predicate from.
        :return: A DictionaryTransform instance.
        """
        if isinstance(arg, DictionaryTransform) and not kwargs:
            return arg
        elif isinstance(arg, DictionaryTransform):
            raise NotImplementedError("Merging DictionaryTransform instance with keyword arguments is not implemented.")
        else:
            return DictionaryTransform(arg, **kwargs)

class ModelTransform:

    def __init__(self, dict_transform: DictionaryTransform) -> None:
        self._dict_transform = dict_transform

    @overload
    def eval(self, source: dict | BaseModel) -> dict: ...
    @overload
    def eval(self, source: list[dict | BaseModel]) -> list[dict]: ...
    def eval(self, source: dict | BaseModel | list[dict | BaseModel]) -> list[dict] | dict:
        if not isinstance(source, list):
            items = [source]
        else:
            items = source

        if len(items) > 0 and isinstance(items[0], BaseModel):
            items = [
                item.model_dump(exclude_unset=True, exclude_none=True, by_alias=True)
                for item in items
            ]

        results = []
        for item in items:
            results.append(self._dict_transform.eval(item))
        
        return results