from __future__ import annotations

from typing import Any, Generic, TypeVar, overload, cast

from ._readonly import _Readonly
from .unset import Unset

T = TypeVar("T")
P = TypeVar("P")

@overload
def resolve(obj: SafeObject[T]) -> T: ...
@overload
def resolve(obj: P) -> P: ...
def resolve(obj: SafeObject[T] | P) -> T | P:
    """Resolve the value of a SafeObject or return the object itself if it's not a SafeObject."""
    if isinstance(obj, SafeObject):
        return obj.__value__
    return obj

def parent(obj: SafeObject[T]) -> SafeObject | None:
    """Get the parent SafeObject of the given SafeObject, or None if there is no parent."""
    return obj.__parent__

class SafeObject(Generic[T], _Readonly):
    """A wrapper around an object that provides safe access to its attributes
    and items, while maintaining a reference to its parent object."""

    def __init__(self, value: Any, parent: SafeObject | None = None):
        """Initialize a SafeObject with a value and an optional parent SafeObject.
        
        :param value: The value to wrap.
        :param parent: The parent SafeObject, if any.
        """
        object.__setattr__(self, "__value__", value)
        if parent and parent._value is not Unset and parent._value is not None:
            object.__setattr__(self, "__parent__", parent)
        else:
            object.__setattr__(self, "__parent__", None)

    def __new__(cls, value: Any, parent: SafeObject | None = None):
        """Create a new SafeObject or return the value directly if it's already a SafeObject.
        
        :param value: The value to wrap.
        :param parent: The parent SafeObject, if any.

        :return: A SafeObject instance or the original value.
        """
        if isinstance(value, SafeObject):
            return value
        return super().__new__(cls)

    def __getattr__(self, name: str) -> Any:
        """Get an attribute of the wrapped object safely.
        
        :param name: The name of the attribute to access.
        :return: The attribute value wrapped in a SafeObject.
        """

        value = resolve(self)
        if isinstance(value, dict):
            return SafeObject(value.get(name, Unset), self)
        attr = getattr(value, name, Unset)
        return SafeObject(attr, self)
    
    def __getitem__(self, key) -> Any:
        """Get an item of the wrapped object safely.

        :param key: The key or index of the item to access.
        :return: The item value wrapped in a SafeObject.
        """

        value = resolve(self)
        value = cast(dict, value)
        if isinstance(value, list):
            return self.__class__(value[key], self)
        return type(self)(value.get(key, Unset), self)

    def __str__(self) -> str:
        """Get the string representation of the wrapped object."""
        return str(resolve(self))
    
    def __repr__(self) -> str:
        """Get the detailed string representation of the SafeObject."""
        value = resolve(self)
        return f"{self.__class__.__name__}({value!r})"