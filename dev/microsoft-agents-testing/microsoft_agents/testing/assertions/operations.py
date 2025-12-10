from typing import TypeVar, Any, Callable

from .dynamic_object import DynamicObject
from .model_query import Selector
from .unset import Unset

# T = TypeVar("T")

# class Functions:

#     @staticmethod
#     def dyn(data: T) -> DynamicObject[T]:
#         return DynamicObject(data)

#     @staticmethod
#     def ref(key: str) -> Callable[[], Any]:
#         def inner(actual: Any) -> Any:
#             return resolve(actual, key)
#         return inner

#     @staticmethod
#     def resolve(data: dict, key: str) -> Callable[[], Any]:
#         def func() -> Any:
#             path = key.split(".")
#             curr = data
#             for part in path:
#                 curr = curr.get(part, Unset)
#                 if curr is Unset:
#                     return Unset
#             return curr
#         return func

# def first(selector_args, func = evaluate):
#     selector = Selector(*selector_args)

#     def inner(data):
#         val = selector.first(data)
#         if val is Unset:
#             return Unset
#         return func(val)