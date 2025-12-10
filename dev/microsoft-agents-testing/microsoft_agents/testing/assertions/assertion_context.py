from __future__ import annotations

import inspect
from typing import Callable, Any

from .types import (
    SafeObject,
    resolve,
    parent
)

from .types import DynamicObject

class AssertionContext:
    """Context for assertions, providing access to actual and baseline data,
    as well as the current path and additional context information."""
    
    def __init__(
            self,
            actual_source: SafeObject,
            baseline_source: Any,
            actual: SafeObject | None = None,
            baseline: Any | None = None,
            context: DynamicObject | None = None,
            path: str = ""
    ):
        """Initialize an AssertionContext.
        
        :param actual_source: The source of the actual data.
        :param baseline_source: The source of the baseline data.
        :param actual: The actual data for this context.
        :param baseline: The baseline data for this context.
        :param context: Additional context information.
        :param path: The current path within the data structures.
        """
        
        self._actual_source = actual_source
        if baseline_source is None:
            baseline_source = {}
            
        self._baseline_source = baseline_source

        if actual is None:
            actual = actual_source
        if baseline is None:
            baseline = baseline_source

        self._actual = actual
        self._baseline = baseline

        if context is None:
            context = DynamicObject({})
        self._context = context

        self._path = path

    def next(self, key: Any) -> AssertionContext:
        """Create a new AssertionContext for the next level in the data structure.
        
        :param key: The key for the next level.
        :return: A new AssertionContext for the next level.
        """
        next_path = f"{self._path}.{key}" if self._path else str(key)
        assert self._baseline is not None
        return AssertionContext(
            self._actual_source,
            self._baseline_source,
            self._actual[key],
            self._baseline[key],
            self._context,
            next_path
        )
    
    def resolve_args(self, query_function: Callable) -> Callable:
        """Resolve the arguments for a query function based on the current context.\
            
        :param query_function: The query function to resolve arguments for.
        :return: A callable with the resolved arguments.
        """
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
