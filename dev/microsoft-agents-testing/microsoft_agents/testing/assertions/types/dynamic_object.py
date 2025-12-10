from __future__ import annotations

from typing import Any, TypeVar, Sized

from .safe_object import SafeObject, resolve, parent
from .unset import Unset

T = TypeVar("T")

PRIMITIVE_TYPES = (int, float, str, bool)
PRIMITIVES = (None, Unset)

class DynamicObject(SafeObject[T]):
    """A wrapper around an object that provides dynamic access to its attributes
    and items, while maintaining a reference to its parent object."""

    def __init__(self, value: Any, parent_object: SafeObject | None = None):
        """Initialize a SafeObject with a value and an optional parent SafeObject.
        
        :param value: The value to wrap.
        :param parent: The parent SafeObject, if any.
        """

        object.__setattr__(self, "__value__", value)
        if parent_object is not None:
            parent_value = resolve(parent_object)
            if parent_value is Unset or parent_value is None:
                parent_object = None
        else:
            parent_object = None
        object.__setattr__(self, "__parent__", parent_object)

    def __new__(cls, value: Any, parent_object: SafeObject | None = None) -> Any:
        """Create a new DynamicObject or return the value directly if it's a primitive type."""
        if isinstance(value, PRIMITIVE_TYPES):
            return value
        elif value in PRIMITIVES:
            return value
        elif isinstance(value, SafeObject) and not isinstance(value, DynamicObject):
            resolved_value = resolve(value)
            parent_object = parent(value)
            return cls.__new__(cls, resolved_value, parent_object)
        return super().__new__(cls, value, parent_object)
    
    
    def __contains__(self, key):
        """Check if the wrapped object contains the given key."""
        value = resolve(self)
        if hasattr(value, "__contains__"):
            return key in value
        raise TypeError(f"{type(value)} object is not iterable")
    
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