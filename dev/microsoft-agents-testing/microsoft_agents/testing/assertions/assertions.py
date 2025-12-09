from __future__ import annotations

from typing import Any

from .types import DynamicObject

class AssertionContext:
    
    def __init__(self, path: str):
        self.path = path
        self._results = []

    @property
    def results(self) -> list:
        return self._results

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

        actual = DynamicObject(actual)

        results = context.results

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                check, msg = Assertions._evaluate_verbose(actual[key], value, context.next(key))
                results.append((check, msg))
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                check, msg = Assertions._evaluate_verbose(actual[i], value, context.next(str(i)))
                results.append((check, msg))
        elif callable(baseline):
            # sig = inspect.signature(baseline)

            # num_args = len(sig.parameters)

            results.append(Assertions.invoke(actual, baseline, context.next(key)))
        else:
            results.append(actual == baseline, f"Values do not match: {actual} != {baseline}")

    @staticmethod
    def evaluate(actual: Any, baseline: Any) -> bool:

        actual = DynamicObject(actual)

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                Assertions.evaluate(actual[key], value)
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                Assertions.evaluate(actual[i], value)
        elif callable(baseline):
            sig = inspect.signature(baseline)

            num_args = len(sig.parameters)

            return baseline()
        else:
            return actual == baseline

        for key, value in baseline.items():
            
            if isinstance(value, dict):
                Assertions.evaluate(actual[key], value)
            elif isinstance(value, list):
                Assertions.evaluate()
            

            if isinstance(value, dict):
                if key not in actual or not isinstance(actual[key], dict):
                    return False
                if not Assertions.evaluate(actual[key], value):
                    return False
            elif isinstance(value, list):
                if key not in actual or not isinstance(actual[key], list):
                    return False
                if len(actual[key]) != len(value):
                    return False
                for i in range(len(value)):
                    if not Assertions.evaluate(actual[key][i], value[i]):
                        return False
            else:
                if key not in actual or actual[key] != value:
                    return False

        if 
        return actual == baseline
        # if callable(word):
        #     sig = inspect.signature(word)

        #     num_args = len(sig.parameters)

        #     return word()
        # else:
        #     return word

    # @staticmethod
    # def evaluate_verbose(actual: Any, baseline: Any) -> str:
    #     if isinstance(actual, dict) and isinstance(baseline, dict):
    #         for key in actual:
    #             if key not in baseline:
    #                 return f"Missing key in baseline: {key}"

    #         for key in baseline:
    #             if key not in actual:
    #                 return f"Missing key in actual: {key}"

    #         for key in actual:
    #             result = Assertions.evaluate_verbose(actual[key], baseline[key])
    #             if result:
    #                 return result

    #         return ""

    #     elif isinstance(actual, list) and isinstance(baseline, list):
    #         if len(actual) != len(baseline):
    #             return f"List lengths do not match: {len(actual)} != {len(baseline)}"

    #         for i in range(len(actual)):
    #             result = Assertions.evaluate_verbose(actual[i], baseline[i])
    #             if result:
    #                 return result

    #         return ""

    #     else:
    #         if actual != baseline:
    #             return f"Values do not match: {actual} != {baseline}"

    #         return ""