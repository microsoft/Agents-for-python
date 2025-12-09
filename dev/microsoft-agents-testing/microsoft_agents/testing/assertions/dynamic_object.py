from typing import Any, Generic, TypeVar

from .unset import Unset

T = TypeVar("T")


class DynamicObject(Generic[T]):

    def __init__(self, value):
        self._value = value

    def __getattribute__(self, name: str) -> Any:
        attr = getattr(self._value, name, Unset)
        if isinstance(attr, (int, float, str, bool)):
            return attr
        return DynamicObject(attr)
    
    def value(self) -> T:
        return self._value

    def __eq__(self, other):
        if isinstance(other, DynamicObject):
            return self._value == other._value
        return self._value == other
    
    def __in__(self, other):
        if isinstance(other, DynamicObject):
            return self._value in other._value
        return self._value in other
    
    def __str__(self):
        return str(self._value)
    
    def __repr__(self):
        return f"DynamicObject({self._value!r})"
