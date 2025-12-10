from __future__ import annotations

from typing import Any, Callable

from .types import SafeObject, DynamicObject, resolve, parent
from .assertion_context import AssertionContext

class Assertions:

    _EVAL_META_FIELD = "__call"

    @staticmethod
    def expand(data: dict) -> dict:
        """Expand a flattened dictionary into a nested dictionary.
        
        :param data: The flattened dictionary to expand.
        :return: The expanded nested dictionary.
        """

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
    def invoke(
            actual: SafeObject[Any],
            query_function: Callable,
            context: AssertionContext
    ) -> tuple[bool, str]:
        """Invoke a query function with resolved arguments.
        
        :param actual: The actual data to pass to the query function.
        :param query_function: The query function to invoke.
        :param context: The current assertion context.
        :return: A tuple containing the result of the query function and a message.
        """

        res = context.resolve_args(query_function)()
    
        if isinstance(res, tuple) and len(res) == 2:
            return res
        else:
            return bool(res), f"Assertion failed for query function: '{query_function.__name__}'"
    
    @staticmethod
    def _check_verbose(actual: SafeObject[Any], baseline: Any, context: AssertionContext) -> tuple[bool, str]:
        """Recursively check the actual data against the baseline data with verbose output.
        
        :param actual: The actual data to check.
        :param baseline: The baseline data to check against.
        :param context: The current assertion context.
        :return: A tuple containing the overall result and a detailed message.
        """

        results = []

        if isinstance(baseline, dict):
            for key, value in baseline.items():
                check, msg = Assertions._check_verbose(actual[key], value, context.next(key))
                results.append((check, msg))
        elif isinstance(baseline, list):
            for i, value in enumerate(baseline):
                check, msg = Assertions._check_verbose(actual[i], value, context.next(i))
                results.append((check, msg))
        elif callable(baseline):
            results.append(Assertions.invoke(actual, baseline, context))
        else:
            check = resolve(actual) == baseline
            msg = f"Values do not match: {actual} != {baseline}" if not check else ""
            results.append((check, msg))
        
        return (all(check for check, msg in results), "\n".join(msg for check, msg in results if not check))

    @staticmethod
    def check_verbose(actual: Any, baseline: Any) -> tuple[bool, str]:
        """Check the actual data against the baseline data with verbose output.
        
        :param actual: The actual data to check.
        :param baseline: The baseline data to check against.
        :return: A tuple containing the overall result and a detailed message.
        """
        actual = SafeObject(actual)
        context = AssertionContext(actual, baseline)
        return Assertions._check_verbose(actual, baseline, context)
    
    @staticmethod
    def check(actual: Any, baseline: Any) -> bool:
        """Check the actual data against the baseline data.
        
        :param actual: The actual data to check.
        :param baseline: The baseline data to check against.
        :return: True if the actual data matches the baseline data, False otherwise.
        """
        return Assertions.check_verbose(actual, baseline)[0]
    
    @staticmethod
    def validate(actual: Any, baseline: Any) -> None:
        """Validate the actual data against the baseline data, raising an assertion error if they do not match.
        
        :param actual: The actual data to validate.
        :param baseline: The baseline data to validate against."
        """
        check, msg = Assertions.check_verbose(actual, baseline)
        assert check, msg