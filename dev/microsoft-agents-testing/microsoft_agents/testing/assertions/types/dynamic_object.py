from __future__ import annotations

from typing import Any, TypeVar, Sized

from .safe_object import SafeObject, resolve
from .unset import Unset

T = TypeVar("T")

PRIMITIVE_TYPES = (int, float, str, bool)
PRIMITIVES = (None, Unset)

class DynamicObject(SafeObject[T]):

    def __new__(cls, value):
        if isinstance(value, PRIMITIVE_TYPES):
            return value
        elif value in PRIMITIVES:
            return value
        return super().__new__(cls, value)

    def __getattr__(self, name: str) -> Any:
        value = resolve(self)
        if isinstance(value, dict):
            return DynamicObject(value.get(name, Unset))
        attr = getattr(value, name, Unset)
        return DynamicObject(attr)
    
    def __getitem__(self, key) -> Any:
        value = resolve(self)
        return DynamicObject(value.get(key, Unset))
    
    def __contains__(self, key):
        value = resolve(self)
        if hasattr(value, "__contains__"):
            return key in value
        raise TypeError(f"{type(value)} object is not iterable")

    def __eq__(self, other) -> bool:
        value = resolve(self)
        other_value = other
        if isinstance(other, SafeObject):
            other_value = resolve(other)
        return value == other_value
    
    def __in__(self, other) -> bool:
        value = resolve(self)
        other_value = other
        if isinstance(other, SafeObject):
            other_value = resolve(other)
        return value in other_value
    
    def __bool__(self) -> bool:
        return bool(resolve(self))
    
    def __len__(self) -> int:
        value = resolve(self)
        if isinstance(value, Sized):
            return len(value)
        raise TypeError(f"{type(value)} object has no length")