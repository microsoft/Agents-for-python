# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any, Generic, TypeVar, overload, cast

from .readonly import Readonly
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
        return object.__getattribute__(obj, "__value__")
    return obj

def parent(obj: SafeObject[T]) -> SafeObject | None:
    """Get the parent SafeObject of the given SafeObject, or None if there is no parent."""
    return object.__getattribute__(obj, "__parent__")

class SafeObject(Generic[T], Readonly):
    """A wrapper that provides safe access to object attributes and items.
    
    SafeObject allows accessing nested attributes and items without raising
    exceptions for missing keys. Instead, it returns Unset for missing values,
    enabling safe chained access like `obj.user.profile.name` even when
    intermediate values don't exist.
    """

    def __init__(self, value: Any, parent_object: SafeObject | None = None):
        """Initialize a SafeObject with a value and an optional parent SafeObject.
        
        :param value: The value to wrap.
        :param parent: The parent SafeObject, if any.
        """

        if isinstance(value, SafeObject):
            return

        object.__setattr__(self, "__value__", value)
        if parent_object is not None:
            parent_value = resolve(parent_object)
            if parent_value is Unset or parent_value is None:
                parent_object = None
        else:
            parent_object = None
        object.__setattr__(self, "__parent__", parent_object)


    def __new__(cls, value: Any, parent_object: SafeObject | None = None):
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
        cls = object.__getattribute__(self, "__class__")
        if isinstance(value, dict):
            return cls(value.get(name, Unset), self)
        attr = getattr(value, name, Unset)
        return cls(attr, self)
    
    def __getitem__(self, key) -> Any:
        """Get an item of the wrapped object safely.

        :param key: The key or index of the item to access.
        :return: The item value wrapped in a SafeObject.
        """

        value = resolve(self)
        value = cast(dict, value)
        if isinstance(value, list):
            cls = object.__getattribute__(self, "__class__")
            return cls(value[key], self)
        if not getattr(value, "__getitem__", None):
            cls = object.__getattribute__(self, "__class__")
            return cls(Unset, self)
        return type(self)(value.get(key, Unset), self)

    def __str__(self) -> str:
        """Get the string representation of the wrapped object."""
        return str(resolve(self))
    
    def __repr__(self) -> str:
        """Get the detailed string representation of the SafeObject."""
        value = resolve(self)
        cls = object.__getattribute__(self, "__class__")
        return f"{cls.__name__}({value!r})"
    
    def __eq__(self, other) -> bool:
        """Check if the wrapped object is equal to another object."""
        value = resolve(self)
        other_value = other
        if isinstance(other, SafeObject):
            other_value = resolve(other)
        return value == other_value
    
    def __call__(self, *args, **kwargs) -> Any:
        """Call the wrapped object if it is callable."""
        value = resolve(self)
        if callable(value):
            result = value(*args, **kwargs)
            cls = object.__getattribute__(self, "__class__")
            return cls(result, self)
        raise TypeError(f"'{type(value).__name__}' object is not callable")