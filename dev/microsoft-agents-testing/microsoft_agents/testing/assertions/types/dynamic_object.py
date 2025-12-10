from __future__ import annotations

from typing import Any, TypeVar, Sized

from .safe_object import SafeObject, resolve
from .unset import Unset

T = TypeVar("T")

PRIMITIVE_TYPES = (int, float, str, bool)
PRIMITIVES = (None, Unset)

class DynamicObject(SafeObject[T]):
    """A wrapper around an object that provides dynamic access to its attributes
    and items, while maintaining a reference to its parent object."""
    

    def __new__(cls, value: Any, parent: SafeObject | None = None) -> Any:
        """Create a new DynamicObject or return the value directly if it's a primitive type."""
        if isinstance(value, PRIMITIVE_TYPES):
            return value
        elif value in PRIMITIVES:
            return value
        return super().__new__(cls, value, parent)
    
    def __contains__(self, key):
        """Check if the wrapped object contains the given key."""
        value = resolve(self)
        if hasattr(value, "__contains__"):
            return key in value
        raise TypeError(f"{type(value)} object is not iterable")

    def __eq__(self, other) -> bool:
        """Check if the wrapped object is equal to another object."""
        value = resolve(self)
        other_value = other
        if isinstance(other, SafeObject):
            other_value = resolve(other)
        return value == other_value
    
    def __in__(self, other) -> bool:
        """Check if the wrapped object is in another object."""
        value = resolve(self)
        other_value = other
        if isinstance(other, SafeObject):
            other_value = resolve(other)
        return value in other_value
    
    def __bool__(self) -> bool:
        """Get the boolean value of the wrapped object."""
        return bool(resolve(self))
    
    def __len__(self) -> int:
        """Get the length of the wrapped object."""
        value = resolve(self)
        if isinstance(value, Sized):
            return len(value)
        raise TypeError(f"{type(value)} object has no length")