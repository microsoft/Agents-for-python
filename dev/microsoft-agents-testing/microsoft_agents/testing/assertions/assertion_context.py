from __future__ import annotations

import inspect
from typing import Callable, Any

from .types.safe_object import (
    SafeObject,
    resolve,
    parent
)

from .types import DynamicObject

class AssertionContext:
    
    def __init__(
            self,
            actual_source: SafeObject,
            actual: SafeObject,
            baseline_source: Any,
            baseline: Any,
            context: DynamicObject | None = None,
            path: str = ""
    ):
        
        self._actual_source = actual_source
        self._actual = actual
        self._baseline_source = baseline_source
        self._baseline = baseline

        if context is None:
            context = DynamicObject({})
        self._context = context

        self._path = path

    def next(self, key: str) -> AssertionContext:
        next_path = f"{self._path}.{key}" if self._path else key
        return AssertionContext(
            self._actual_source,
            self._actual[key],
            self._baseline_source,
            self._baseline[key],
            self._context,
            next_path
        )
    
    def resolve_args(self, query_function: Callable) -> Callable:
        sig = inspect.getfullargspec(query_function)
        args = {}

        args_map = {
            "actual": DynamicObject(self._actual_source),
            "path": self._path,
            "value": self._actual,
            "parent": parent(self._actual),
            "context": self._context,
        }

        for arg in sig.args:
            if arg in args_map:
                args[arg] = args_map[arg]
            else:
                raise RuntimeError(f"Unknown argument '{arg}' in query function")
            
        output_func = query_function(**args)
        output_func.__name__ = query_function.__name__
        return output_func
