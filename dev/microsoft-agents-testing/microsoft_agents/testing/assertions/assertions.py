from __future__ import annotations

from typing import Any, Callable

from .types import SafeObject

class AssertionContext:
    
    def __init__(self, path: str = ""):
        self.path = path

    def next(self, key: str) -> AssertionContext:
        next_path = f"{self.path}.{key}" if self.path else key
        return AssertionContext(next_path)

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
    def _evaluate_verbose(actual: Any, baseline: Any, context: AssertionContext) -> tuple[bool, str]:

        results = []

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                check, msg = Assertions._evaluate_verbose(actual[key], value, context.next(key))
                results.append((check, msg))
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                check, msg = Assertions._evaluate_verbose(actual[i], value, context.next(str(i)))
                results.append((check, msg))
        elif callable(baseline):
            results.append(Assertions.invoke(actual.resolve(), baseline, context))
        else:
            check = actual.resolve() == baseline
            msg = f"Values do not match: {actual} != {baseline}" if not check else ""
            results.append((check, msg))
        
        return (all(check for check, msg in results), "\n".join(msg for check, msg in results if not check))

    @staticmethod
    def evaluate_verbose(actual: Any, baseline: Any) -> tuple[bool, str]:
        actual = SafeObject(actual)
        return Assertions._evaluate_verbose(actual, baseline, AssertionContext())
    
    @staticmethod
    def evaluate(actual: Any, baseline: Any) -> bool:
        return Assertions.evaluate_verbose(actual, baseline)[0]
    
    @staticmethod
    def validate(actual: Any, baseline: Any) -> None:
        check, msg = Assertions.evaluate_verbose(actual, baseline)
        assert check, msg
    
    @staticmethod
    def invoke(actual: Any, baseline: Callable, context: AssertionContext) -> tuple[bool, str]:
        try:
            result = baseline(actual)
            return (result, "")
        except Exception as e:
            return (False, f"Error in evaluation at {context.path}: {e}")