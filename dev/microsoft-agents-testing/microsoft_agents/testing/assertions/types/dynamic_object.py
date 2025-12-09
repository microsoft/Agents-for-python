from __future__ import annotations

from typing import Any, TypeVar

from .safe_object import SafeObject
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
        if isinstance(self._value, dict):
            return DynamicObject(self._value.get(name, Unset))
        attr = getattr(self._value, name, Unset)
        return DynamicObject(attr)
    
    def __getitem__(self, key) -> Any:
        return DynamicObject(self._value.get(key, Unset))