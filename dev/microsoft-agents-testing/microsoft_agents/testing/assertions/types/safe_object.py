from __future__ import annotations

from typing import Any, Generic, TypeVar

from ._readonly import _Readonly
from .unset import Unset

T = TypeVar("T")

class SafeObject(Generic[T], _Readonly):

    def __init__(self, value):
        object.__setattr__(self, "_value", value)

    def __new__(cls, value):
        if isinstance(value, SafeObject):
            return value
        return super().__new__(cls)

    def __getattr__(self, name: str) -> Any:
        if isinstance(self._value, dict):
            return SafeObject(self._value.get(name, Unset))
        attr = getattr(self._value, name, Unset)
        return SafeObject(attr)
    
    def __getitem__(self, key) -> Any:
        if isinstance(self._value, list):
            return SafeObject(self._value[key])
        return SafeObject(self._value.get(key, Unset))
    
    def resolve(self) -> T:
        return self._value
    
    def __contains__(self, key):
        if hasattr(self._value, "__contains__"):
            return key in self._value
        raise TypeError(f"{type(self._value)} object is not iterable")

    def __eq__(self, other):
        if isinstance(other, SafeObject):
            return self._value == other._value
        return self._value == other
    
    def __in__(self, other):
        if isinstance(other, SafeObject):
            return self._value in other._value
        return self._value in other
    
    def __str__(self):
        return str(self._value)
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self._value!r})"
    
    def __len__(self):
        if hasattr(self._value, "__len__"):
            return len(self._value)
        raise TypeError(f"{type(self._value)} object has no length")