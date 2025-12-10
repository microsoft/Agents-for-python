from __future__ import annotations

from typing import Any, Generic, TypeVar, overload

from ._readonly import _Readonly
from .unset import Unset

T = TypeVar("T")
P = TypeVar("P")

@overload
def resolve(obj: SafeObject[T]) -> T: ...
@overload
def resolve(obj: P) -> P: ...
def resolve(obj: SafeObject[T] | P) -> T | P:
    if isinstance(obj, SafeObject):
        return obj.__value__
    return obj

def parent(obj: SafeObject[T]) -> SafeObject | None:
    return obj.__parent__

class SafeObject(Generic[T], _Readonly):

    def __init__(self, value, parent: SafeObject | None = None):
        object.__setattr__(self, "__value__", value)
        if parent and parent._value is not Unset and parent._value is not None:
            object.__setattr__(self, "__parent__", parent)
        else:
            object.__setattr__(self, "__parent__", None)

    def __new__(cls, value):
        if isinstance(value, SafeObject):
            return value
        return super().__new__(cls)

    def __getattr__(self, name: str) -> Any:
        value = resolve(self)
        if isinstance(value, dict):
            return SafeObject(value.get(name, Unset), self)
        attr = getattr(value, name, Unset)
        return SafeObject(attr, self)
    
    def __getitem__(self, key) -> Any:
        value = resolve(self)
        if isinstance(value, list):
            return self.__class__(value[key], self)
        return type(self)(value.get(key, Unset), self)

    def __str__(self) -> str:
        return str(resolve(self))
    
    def __repr__(self) -> str:
        value = resolve(self)
        return f"{self.__class__.__name__}({value!r})"