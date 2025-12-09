from typing import Any, Callable, TypeVar
import inspect

from azure.core import rest

from .dynamic_object import DynamicObject
from .unset import Unset

T = TypeVar("T")

def dyn(data: T) -> DynamicObject[T]:
    return DynamicObject(data)

def ref(key: str) -> Callable[[], Any]:
    def inner(actual: Any) -> Any:
        return evaluate(actual, key)
    return inner

def resolve(data: dict, key: str) -> Any:
    path = key.split(".")
    curr = data
    for part in path:
        curr = curr.get(part, Unset)
        if curr is Unset:
            return Unset
    return curr

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

            if root not in new_data:
                new_data[root] = {}

            new_data[root][path] = value

        else:
            root = key
            if root in data:
                raise RuntimeError()

            new_data[root] = value

    # expand
    for key, value in new_data.items():
        new_data[key] = expand(value)

    return new_data

def evaluate(actual: Any, word: Any) -> Any:
    if callable(word):
        sig = inspect.signature(word)

        num_args = len(sig.parameters)

        return word()
    else:
        return word