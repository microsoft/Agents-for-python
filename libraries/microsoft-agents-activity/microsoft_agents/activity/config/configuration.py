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
    get_type_hints,
    overload,
)

class _MISSING_CLS:
    pass
_MISSING = _MISSING_CLS()

T = TypeVar("T")

class _IConfigurationCls(Protocol, Generic[T]):
    def __init__(self: T, config: Mapping) -> None:
        ...

class _IConfigurationFactory(Protocol, Generic[T]):
    def __call__(self, config: Mapping) -> T:
        ...
        
# def _missing(val: Any) -> TypeGuard[__MISSING]:
#     return isinstance(val, __MISSING)

class Configuration(dict):
    """A configuration class that extends the built-in dict with additional functionality for handling nested configurations."""

    def __init__(self, original: Mapping, _base_path: str | None = None, **kwargs):
        """Initialize a Configuration instance.

        :param original: The original mapping to initialize the configuration from.
        :param _base_path: The base path for resolving nested configuration keys.
        """
        self.__dict__ = original.__dict__
        self._base_path = _base_path or ""

    def _resolve_path(self, key: str) -> str:
        """Resolve a configuration path by combining the base path and the key."""
        return f"{self._base_path}.{key}" if self._base_path else key

    def _get(self, key: str) -> Any:
        """Retrieve a value from the configuration by key, returning _MISSING if not found."""
        return super().get(key, _MISSING)

    def __getitem__(self, key: str) -> Any:
        """Retrieve a value from the configuration by key, raising KeyError if not found."""
        val = self._get(key)
        if val is _MISSING:
            raise KeyError(key)
        return val

    def _get_typed(self, key: str, val: Any,  *, cls: type[T], factory: Callable[[Any], T] | None = None) -> T:
        """Retrieve a value from the configuration by key, ensuring it is of the specified type."""
        if isinstance(val, cls):
            return val
        if factory:
            new_val = factory(val)
            if isinstance(new_val, cls):
                return new_val
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
        if val is _MISSING:
            if isinstance(default, _MISSING_CLS):
                raise KeyError(section)
            return default

        if isinstance(val, Configuration) and val._base_path == self._resolve_path(section):
            return val
        elif isinstance(val, Configuration):
            return Configuration(val, _base_path=self._resolve_path(section))
        elif isinstance(val, Mapping):
            return  Configuration(val, _base_path=self._resolve_path(section))
        raise TypeError(f"Section {section} is not a mapping")

    @overload
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: _IConfigurationFactory, default: _MISSING_CLS = _MISSING) -> T:
        ...
    @overload
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: _IConfigurationFactory, default: T | None) -> T | None:
        ...
    @overload
    def get_typed(self, _type: type[T], key: str | None = None, *, factory: _IConfigurationFactory | None, default: T | _MISSING_CLS) -> T:
        ...
    @overload
    def get_typed(self, _type: type[_IConfigurationCls], key: str | None = None, *, factory: None = None, default: T | None | _MISSING_CLS = _MISSING) -> T | None:
        ...
    def get_typed(self, _type: type[T | _IConfigurationCls], key: str | None = None, *, factory: _IConfigurationFactory | None = None, default: T | None | _MISSING_CLS = _MISSING) -> T | None:
        """Retrieve a typed value from the configuration, converting it to the specified class if necessary.

        :param _type: The expected type of the section.
        :param key: The key of the section to retrieve. If None, uses the type name as the key.
        :param factory: The factory to convert the section with, if necessary.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as an instance of the specified type, or the default value if not found.
        :raises TypeError: If the return type of the class is not a subclass of the expected type.
        """

        if _type is Configuration or factory is Configuration:
            raise TypeError("Use Configuration.get_section instead when retrieving a Configuration section")

        factory = factory or _type

        key = key or _type.__name__
        val = self._get(key)
        if isinstance(val, _MISSING_CLS):
            if isinstance(default, _MISSING_CLS):
                raise KeyError(key)
            return default

        try:
            return self._get_typed(key, val, cls=_type, factory=factory)
        except Exception as e:
            raise TypeError(f"Failed to convert section {key} using factory {factory}: {e}")