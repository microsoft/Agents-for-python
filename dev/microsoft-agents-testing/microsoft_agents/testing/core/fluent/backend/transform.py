# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transform classes for converting and evaluating model data.

Provides DictionaryTransform and ModelTransform for applying callable
transformations to dictionary and model data structures.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, overload, TypeVar, cast

from pydantic import BaseModel

from .types import Unset, SafeObject, resolve, parent
from .utils import expand, flatten

T = TypeVar("T")

class DictionaryTransform:
    """Transform that applies callable predicates to dictionary values.
    
    Supports dot-notation keys for nested access (e.g., 'user.profile.name').
    String values starting with '~' are converted to substring match predicates.
    
    Example::
    
        dt = DictionaryTransform({"type": "message", "text": "~hello"})
        result = dt.eval({"type": "message", "text": "hello world"})
        # result == {"type": True, "text": True}
    """

    DT_ROOT_CALLABLE_KEY = '__DT_ROOT_CALLABLE_KEY'
    
    def __init__(self, arg: dict | Callable | None, **kwargs) -> None:

        if not isinstance(arg, (dict, Callable)) and arg is not None:
            raise ValueError("Argument must be a dictionary or callable.")

        if isinstance(arg, dict) or arg is None:
            temp = arg or {}
        else:
            temp = {}

        if callable(arg):
            temp[self.DT_ROOT_CALLABLE_KEY] = arg

        flat_root = flatten(temp)
        flat_kwargs = flatten(kwargs)

        combined = {**flat_root, **flat_kwargs}
        for key, val in combined.items():
            if isinstance(val, Callable):
                flat_root[key] = val
            else:
                if isinstance(val, str) and val.startswith("~"):
                    _substring = val[1:]
                    flat_root[key] = lambda x, _sub=_substring: _sub in x
                else:
                    _expected = val
                    flat_root[key] = lambda x, _exp=_expected: x == _exp

        self._map = flat_root

    @property
    def map(self) -> dict[str, Callable[..., Any]]:
        return self._map 

    @staticmethod
    def _get(actual: dict, key: str) -> Any:
        keys = key.split(".")
        current = SafeObject(actual)
        for k in keys:
            current = current[k]
        return resolve(current)

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
        
    def eval(self, actual: dict, root_callable_arg: Any=None) -> dict:        
        result = {}

        # Create a wrapper dict to avoid modifying the original object
        # This handles cases where actual is not a mutable dict (e.g., Pydantic models, custom objects)
        if isinstance(actual, dict):
            eval_context = dict(actual)
        else:
            eval_context = {}
        
        if root_callable_arg is not None:
            eval_context[DictionaryTransform.DT_ROOT_CALLABLE_KEY] = root_callable_arg 
        else:
            eval_context[DictionaryTransform.DT_ROOT_CALLABLE_KEY] = actual
        for key, func in self._map.items():
            if not callable(func):
                raise RuntimeError(f"Predicate value for key '{key}' is not callable")
            result[key] = self._invoke(eval_context, key, func)

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
    """Apply a DictionaryTransform to BaseModel or dict instances.
    
    Handles conversion of Pydantic models to dictionaries before
    applying the underlying DictionaryTransform.
    """

    def __init__(self, dict_transform: DictionaryTransform) -> None:
        self._dict_transform = dict_transform

    @overload
    def eval(self, source: dict | BaseModel) -> dict: ...
    @overload
    def eval(self, source: list[dict] | list[BaseModel]) -> list[dict]: ...
    def eval(self, source: dict | BaseModel | list[dict] | list[BaseModel]) -> list[dict] | dict:
        if not isinstance(source, list):
            source = cast(list[dict] | list[BaseModel], [source])
            items = source
        else:
            items = cast(list[dict] | list[BaseModel], source)

        if len(items) > 0 and isinstance(items[0], BaseModel):
            items = cast(list[BaseModel], items)
            items = [
                item.model_dump(exclude_unset=True, exclude_none=True, by_alias=True)
                for item in items
            ]
        items = cast(list[dict], items)

        results = []
        for i, item in enumerate(items):
            results.append(self._dict_transform.eval(item, source[i]))
        
        return results