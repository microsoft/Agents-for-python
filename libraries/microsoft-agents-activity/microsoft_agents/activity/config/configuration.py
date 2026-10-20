# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Protocol,
    TypeGuard,
    TypeVar,
    overload,
)

from ._configuration_protocol import _ConfigurationProtocol
from ._utils import _MISSING_CLS, _MISSING, _is_missing, _get

T = TypeVar("T")
_ConfigurationProtocolT = TypeVar("_ConfigurationProtocolT", bound=_ConfigurationProtocol)

class Configuration(dict, _ConfigurationProtocol):
    """A configuration class that extends the built-in dict with additional functionality for handling nested configurations."""

    def __init__(self, original: dict, _base_path: str | None = None, **kwargs):
        """Initialize a Configuration instance.

        :param original: The original mapping to initialize the configuration from.
        :param _base_path: The base path for resolving nested configuration keys.
        """
        self.__dict__ = original.__dict__
        self._base_path = _base_path or ""

    @classmethod
    def from_mapping(cls, mapping: Mapping, _base_path: str | None = None) -> Configuration:
        return cls(dict(mapping), _base_path=_base_path)

    def _resolve_path(self, key: str) -> str:
        """Resolve a configuration path by combining the base path and the key."""
        return f"{self._base_path}.{key}" if self._base_path else key

    def _get(self, key: str) -> Any:
        """Retrieve a value from the configuration by key, returning _MISSING if not found."""
        return _get(self, key, _MISSING)

    def _get_typed(self, key: str, *, cls: type[T], factory: Callable[[Any], T] | None = None, default: T | _MISSING_CLS = _MISSING) -> T:
        """Retrieve a value from the configuration by key, ensuring it is of the specified type.
        
        :param key: The key to retrieve.
        :param cls: The expected type of the value.
        :param factory: An optional factory function to convert the value to the expected type.
        :param default: The default value to return if the key is not found or the value is not of the expected type.
        """

        val = self._get(key)

        if isinstance(val, cls):
            return val
        if factory:
            new_val = factory(val)
            if isinstance(new_val, cls):
                return new_val
            else:
                raise TypeError(f"Factory for key {key} did not return an instance of {cls.__name__}.")
        if not _is_missing(default):
            return default
        raise TypeError(f"Value for key {key} is not of type {cls.__name__} and could not be converted.")

    @overload
    def get_section(self, section: str, default: Configuration | _MISSING_CLS = _MISSING) -> Configuration:
        ...
    @overload
    def get_section(self, section: str, default: None) -> Configuration | None:
        ...
    def get_section(self, section: str, default: Configuration | None | _MISSING_CLS = _MISSING) -> Configuration | None:
        """Retrieve a section of the configuration, returning it as a Configuration object.
        
        :param section: The name of the section to retrieve.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as a Configuration object, or the default value if not found.
        :raises KeyError: If the section is not found and no default is provided.
        :raises TypeError: If the section is found but is not a mapping.
        """
        val = self._get(section)
        if _is_missing(val):
            if _is_missing(default):
                raise KeyError(section)
            return default

        if isinstance(val, Configuration):
            return val
        elif isinstance(val, Mapping):
            return  Configuration.from_mapping(val, _base_path=self._resolve_path(section))
        raise TypeError(f"Section {section} is not a mapping")

    @overload
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: Callable[[Mapping], T], default: _MISSING_CLS = _MISSING) -> T:
        ...
    @overload
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: Callable[[Mapping], T], default: T | None) -> T | None:
        ...
    @overload
    def get_typed(self, _type: type[_ConfigurationProtocolT], key: str | None = None, *, factory: None = None, default: _ConfigurationProtocolT | _MISSING_CLS) -> _ConfigurationProtocolT:
        ...
    @overload
    def get_typed(self, _type: type[_ConfigurationProtocolT], key: str | None = None, *, factory: None = None, default: _ConfigurationProtocolT | None | _MISSING_CLS = _MISSING) -> _ConfigurationProtocolT | None:
        ...
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: Callable[[Mapping], T] | None = None, default: T | None | _MISSING_CLS = _MISSING) -> T | None:
        """Retrieve a typed value from the configuration, converting it to the specified class if necessary.

        :param _type: The expected type of the section.
        :param key: The key of the section to retrieve. If None, uses the type name as the key.
        :param factory: The factory to convert the section with, if necessary.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as an instance of the specified type, or the default value if not found.
        :raises TypeError: If the return type of the class is not a subclass of the expected type.
        """
        key = key or _type.__name__
        val = self._get(key)
        if _is_missing(val):
            if _is_missing(default):
                raise KeyError(key)
            return default

        if not isinstance(val, Mapping):
            raise TypeError(f"Section {key} is not a mapping. This may be supported in the future.")

        if not factory:
            if isinstance(_type, _ConfigurationProtocol):
                return _type.from_mapping(val)
            raise ValueError(f"Type {_type} is not a subclass of _ConfigurationProtocol and no factory was provided")

        return factory(val)