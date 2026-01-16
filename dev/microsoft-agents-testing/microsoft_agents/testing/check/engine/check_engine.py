import inspect
from typing import Any, Callable, Protocol

from pydantic import BaseModel

from .check_context import CheckContext
from .types import (
    SafeObject,
    resolve,
    parent,
    Unset,
)

DEFAULT_FIXTURES = {
    "actual": lambda ctx: ctx.actual,
    "baseline": lambda ctx: ctx.baseline,
    "path": lambda ctx: ctx.path,
    "root_actual": lambda ctx: ctx.root_actual,
    "root_baseline": lambda ctx: ctx.root_baseline,
}

class QueryFunction(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> bool | tuple[bool, str]: ...

class CheckEngine:

    def __init__(self, fixtures: dict[str, Callable[[CheckContext], Any]] | None = None):
        self._fixtures = fixtures or DEFAULT_FIXTURES

    def resolve_args(self, query_function: Callable, context: CheckContext) -> Callable:
        """Resolve the arguments for a query function based on the current context.\
            
        :param query_function: The query function to resolve arguments for.
        :param context: The current assertion context. 
        :return: A callable with the resolved arguments.
        """
        sig = inspect.getfullargspec(query_function)
        args = {}

        for arg in sig.args:
            if arg in self._fixtures:
                args[arg] = self._fixtures[arg](context)
            else:
                raise RuntimeError(f"Unknown argument '{arg}' in query function")
            
        output_func = query_function(**args)
        output_func.__name__ = query_function.__name__
        return output_func
    
    def invoke(self, query_function: Callable, context: CheckContext) -> Any:

        sig = inspect.getfullargspec(query_function)
        args = {}

        for arg in sig.args:
            if arg in self._fixtures:
                args[arg] = self._fixtures[arg](context)
            else:
                raise RuntimeError(f"Unknown argument '{arg}' in query function")

        res = query_function(**args)
        if isinstance(res, tuple) and len(res) == 2:
            return res[0], res[1]
        else:
            return bool(res), f"Assertion failed for query function: '{query_function.__name__}'"
        
    def _check_verbose(self, actual: SafeObject[Any], baseline: Any, context: CheckContext) -> tuple[bool, str]:
        """Recursively check the actual data against the baseline data with verbose output.
        
        :param actual: The actual data to check.
        :param baseline: The baseline data to check against.
        :param context: The current assertion context.
        :return: A tuple containing the overall result and a detailed message.
        """

        results = []

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                check, msg = self._check_verbose(actual[key], value, context.child(key))
                results.append((check, msg))
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                check, msg = self._check_verbose(actual[i], value, context.child(i))
                results.append((check, msg))
        elif callable(baseline):
            results.append(self.invoke(baseline, context))
        else:
            check = resolve(actual) == baseline
            msg = f"Values do not match: {actual} != {baseline}" if not check else ""
            results.append((check, msg))
        
        return (all(check for check, msg in results), "\n".join(msg for check, msg in results if not check))
        
    def check_verbose(self, actual: Any, baseline: Any) -> tuple[bool, str]:

        if isinstance(actual, BaseModel):
            actual = actual.model_dump(exclude_unset=True)
        if isinstance(baseline, BaseModel):
            baseline = baseline.model_dump(exclude_unset=True)

        actual = SafeObject(actual)
        context = CheckContext(actual, baseline)
        
        return self._check_verbose(actual, baseline, context)
        
    def check(self, actual: Any, baseline: Any) -> bool:
        return self.check_verbose(actual, baseline)[0]

    def validate(self, actual: Any, baseline: Any) -> None:
        res, msg = self.check_verbose(actual, baseline)
        assert res, msg