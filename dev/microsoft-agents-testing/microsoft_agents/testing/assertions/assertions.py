from __future__ import annotations

import inspect
from pathlib import PurePath
from typing import Any, Callable

from .types import SafeObject, DynamicObject
from .assertion_context import AssertionContext

class Assertions:

    _EVAL_META_FIELD = "__call"

    @staticmethod
    def expand(data: dict) -> dict:

        if not isinstance(data, dict):
            return data

        new_data = {}

        # flatten
        for key, value in data.items():
            if "." in key:
                index = key.index(".")
                root = key[:index]
                path = key[index + 1 :]

                if root in new_data and path in new_data[root]:
                    raise RuntimeError()
                elif root in new_data and not isinstance(new_data[root], (dict, list)):
                    raise RuntimeError()

                if root not in new_data:
                    new_data[root] = {}

                new_data[root][path] = value

            else:
                root = key
                if root in new_data:
                    raise RuntimeError()

                new_data[root] = value

        # expand
        for key, value in new_data.items():
            new_data[key] = Assertions.expand(value)

        return new_data

    @staticmethod
    def _next_path(path: str, key: str) -> str:
        if path:
            return f"{path}.{key}"
        else:
            return key
        
    @staticmethod
    def invoke(
            actual: SafeObject[Any],
            query_function: Callable,
            context: AssertionContext
    ) -> tuple[bool, str]:

        res = context.resolve_args(query_function)()
    
        if isinstance(res, tuple) and len(res) == 2:
            return res
        else:
            return bool(res), f"Assertion failed for query function: '{query_function.__name__}'"
    
    @staticmethod
    def _check_verbose(actual: SafeObject[Any], baseline: Any, context: AssertionContext) -> tuple[bool, str]:

        results = []

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                check, msg = Assertions._check_verbose(actual[key], value, context.next(key))
                results.append((check, msg))
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                check, msg = Assertions._check_verbose(actual[i], value, context.next(str(i)))
                results.append((check, msg))
        elif callable(baseline):
            results.append(Assertions.invoke(actual, baseline, context))
        else:
            check = actual.resolve() == baseline
            msg = f"Values do not match: {actual} != {baseline}" if not check else ""
            results.append((check, msg))
        
        return (all(check for check, msg in results), "\n".join(msg for check, msg in results if not check))

    @staticmethod
    def check_verbose(actual: Any, baseline: Any) -> tuple[bool, str]:
        actual = SafeObject(actual)
        context = AssertionContext(actual, baseline)
        return Assertions._check_verbose(actual, baseline, context)
    
    @staticmethod
    def check(actual: Any, baseline: Any) -> bool:
        return Assertions.check_verbose(actual, baseline)[0]
    
    @staticmethod
    def validate(actual: Any, baseline: Any) -> None:
        check, msg = Assertions.check_verbose(actual, baseline)
        assert check, msg