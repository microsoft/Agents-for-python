from __future__ import annotations

from typing import Any, Callable
from dataclasses import dataclass

from .safe_object import SafeObject

DEFAULT_FIXTURES = {
    "actual": lambda ctx: ctx.actual,
    "baseline": lambda ctx: ctx.baseline,
    "path": lambda ctx: ctx.path,
    "root_actual": lambda ctx: ctx.root_actual,
    "root_baseline": lambda ctx: ctx.root_baseline,
}

class AssertionContext:

    def __init__(
        self,
        actual: SafeObject,
        baseline: Any,
        fixture_map: dict[str, Callable[[AssertionContext], Any]] | None = None
    ):
        
        self.actual = actual
        self.baseline = baseline
        self.path = []
        self.root_actual = actual
        self.root_baseline = baseline
        self._fixture_map = fixture_map or DEFAULT_FIXTURES

    def child(self, key: Any) -> AssertionContext:

        child_ctx = AssertionContext(
            actual=self.actual[key],
            baseline=self.baseline[key],
            fixture_map=self._fixture_map
        )
        child_ctx.path = self.path + [key]
        child_ctx.root_actual = self.root_actual
        child_ctx.root_baseline = self.root_baseline
        return child_ctx
    
    def resolve_args(self, query_function: Callable) -> Callable:
        """Resolve the arguments for a query function based on the current context.\
            
        :param query_function: The query function to resolve arguments for.
        :return: A callable with the resolved arguments.
        """
        sig = inspect.getfullargspec(query_function)
        args = {}

        for arg in sig.args:
            if arg in self._fixture_map:
                args[arg] = self._fixture_map[arg](self)
            else:
                raise RuntimeError(f"Unknown argument '{arg}' in query function")
            
        output_func = query_function(**args)
        output_func.__name__ = query_function.__name__
        return output_func