# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
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
from typing_extensions import Self

from ._configuration_protocol import _ConfigurationProtocol
from ._constants import _PATH_SEPARATOR
from ._utils import (
    _MISSING_CLS,
    _MISSING,
    _get,
    _handle_bool,
    _handle_int,
    _handle_float,
    _handle_str,
    _is_missing,
    _resolve,
)

T = TypeVar("T")
_ConfigurationProtocolT = TypeVar(
    "_ConfigurationProtocolT", bound=_ConfigurationProtocol
)


class Configuration(dict, _ConfigurationProtocol):
    """A configuration class that extends the built-in dict with additional functionality for handling nested configurations."""

    def __init__(self, original: dict | None = None, _base_path: str | None = None, **kwargs):
        """Initialize a Configuration instance.

        :param _original: The original mapping to initialize the configuration from.
        :param _base_path: The base path for resolving nested configuration keys.
        """
        if original is not None and kwargs:
            raise ValueError("Cannot provide both 'original' and keyword arguments.")
        super().__init__(original or kwargs)
        self._base_path = _base_path or ""
        
    @classmethod
    def from_mapping(
        cls, _mapping: Mapping | None = None, _base_path: str | None = None, **kwargs
    ) -> Configuration:
        if isinstance(_mapping, Configuration) and not kwargs:
            return _mapping
        if kwargs:
            if not _mapping:
                resolved = kwargs
            else:
                resolved = _resolve(_mapping, kwargs, path_transformer=lambda x: x)
        else:
            resolved = _mapping
        return cls(resolved, _base_path=_base_path)

    @classmethod
    def from_config(self, base: Configuration | None, **kwargs) -> Configuration:
        """Create a new Configuration instance by forking the current configuration with additional key-value pairs."""
        if base is None:
            return Configuration(**kwargs)
        new_config = base.copy()
        return Configuration.from_mapping(new_config, _base_path=base._base_path, **kwargs)

    def _resolve_path(self, key: str) -> str:
        """Resolve a configuration path by combining the base path and the key."""
        return f"{self._base_path}{_PATH_SEPARATOR}{key}" if self._base_path else key

    def _get(self, *keys: str, default: Any = _MISSING, skip_none: bool = False) -> Any:
        """Retrieve a value from the configuration by key, returning _MISSING if not found."""
        res = _get(self, *keys, default=_MISSING, skip_none=skip_none)
        if _is_missing(res):
            if _is_missing(default):
                raise KeyError(keys[0])
            return default
        return res

    def _get_typed(
        self,
        *keys: str,
        cls: type[T],
        factory: Callable[[Any], T] | None = None,
        default: T | _MISSING_CLS = _MISSING,
    ) -> T:
        """Retrieve a value from the configuration by key, ensuring it is of the specified type.

        :param key: The key to retrieve.
        :param cls: The expected type of the value.
        :param factory: An optional factory function to convert the value to the expected type.
        :param default: The default value to return if the key is not found or the value is not of the expected type.
        """

        val = self._get(*keys)

        if isinstance(val, cls):
            return val
        if factory:
            new_val = factory(val)
            if isinstance(new_val, cls):
                return new_val
            else:
                raise TypeError(
                    f"Factory for key {key} did not return an instance of {cls.__name__}."
                )
        if not _is_missing(default):
            return default
        raise TypeError(
            f"Value for key {key} is not of type {cls.__name__} and could not be converted."
        )

    @overload
    def get_section(
        self, section: str, default: Configuration | _MISSING_CLS = _MISSING
    ) -> Configuration: ...
    @overload
    def get_section(self, section: str, default: None) -> Configuration | None: ...
    def get_section(
        self, section: str, default: Configuration | None | _MISSING_CLS = _MISSING
    ) -> Configuration | None:
        """Retrieve a section of the configuration, returning it as a Configuration object.

        :param section: The name of the section to retrieve.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as a Configuration object, or the default value if not found.
        :raises KeyError: If the section is not found and no default is provided.
        :raises TypeError: If the section is found but is not a mapping.
        """
        val = self._get(section, default)

        if isinstance(val, Configuration):
            return val
        elif isinstance(val, Mapping):
            return Configuration.from_mapping(
                val, _base_path=self._resolve_path(section)
            )
        raise TypeError(f"Section {section} is not a mapping")

    @overload
    def get_typed(
        self,
        _type: type[T],
        key: str | None = None,
        *,
        factory: Callable[[Mapping], T] | None = None,
        default: T | _MISSING_CLS = _MISSING,
    ) -> T: ...
    @overload
    def get_typed(
        self,
        _type: type[T],
        key: str | None = None,
        *,
        factory: Callable[[Mapping], T],
        default: None,
    ) -> T | None: ...
    @overload
    def get_typed(
        self,
        _type: type[_ConfigurationProtocolT],
        key: str | None = None,
        *,
        factory: None = None,
        default: _ConfigurationProtocolT | _MISSING_CLS,
    ) -> _ConfigurationProtocolT: ...
    @overload
    def get_typed(
        self,
        _type: type[_ConfigurationProtocolT],
        key: str | None = None,
        *,
        factory: None = None,
        default: _ConfigurationProtocolT | None | _MISSING_CLS = _MISSING,
    ) -> _ConfigurationProtocolT | None: ...
    def get_typed(
        self,
        _type: type[T],
        key: str | None = None,
        *,
        factory: Callable[[Mapping], T] | None = None,
        default: T | None | _MISSING_CLS = _MISSING,
    ) -> T | None:
        """Retrieve a typed value from the configuration, converting it to the specified class if necessary.

        :param _type: The expected type of the section.
        :param key: The key of the section to retrieve. If None, uses the type name as the key.
        :param factory: The factory to convert the section with, if necessary.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as an instance of the specified type, or the default value if not found.
        :raises TypeError: If the return type of the class is not a subclass of the expected type.
        """
        key = key or _type.__name__
        val = self._get(key, default)

        if not isinstance(val, Mapping):
            raise TypeError(
                f"Section {key} is not a mapping. This may be supported in the future."
            )

        if not factory:
            if isinstance(_type, _ConfigurationProtocol):
                return _type.from_mapping(val)
            raise ValueError(
                f"Type {_type} is not a subclass of _ConfigurationProtocol and no factory was provided"
            )

        return factory(val)

    @overload
    def get_bool(self, *keys: str, default: bool | _MISSING_CLS = _MISSING) -> bool:
        ...
    @overload
    def get_bool(self, *keys: str, default: None = None) -> bool | None:
        ...
    def get_bool(self, *keys: str, default: bool | None | _MISSING_CLS = _MISSING) -> bool | None:
        """Retrieve a boolean value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
        """
        val = self._get(*keys, default=default, skip_none=True)
        return _handle_bool(val, default, keys[0])

    def get_booln(self, *keys: str, default: bool | None = None) -> bool | None:
        """Retrieve a boolean value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
        """
        return self.get_bool(*keys, default=default)

    @overload
    def get_int(self, *keys: str, default: None = None) -> int | None:
        ...
    @overload
    def get_int(self, *keys: str, default: int | _MISSING_CLS = _MISSING) -> int:
        ...
    def get_int(self, *keys: str, default: int | None | _MISSING_CLS = _MISSING) -> int | None:
        """Retrieve an integer value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        val = self._get(*keys, default=default, skip_none=True)
        return _handle_int(val, default, keys[0])

    def get_intn(self, *keys: str, default: int | None = None) -> int | None:
        """Retrieve an integer value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        return self.get_int(*keys, default=default)

    @overload
    def get_float(self, *keys: str, default: None = None) -> float | None:
        ...
    @overload
    def get_float(self, *keys: str, default: float | _MISSING_CLS = _MISSING) -> float:
        ...
    def get_float(self, *keys: str, default: float | None | _MISSING_CLS = _MISSING) -> float | None:
        """Retrieve a float value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
        val = self._get(*keys, default=default, skip_none=True)
        return _handle_float(val, default, keys[0])

    def get_floatn(self, *keys: str, default: float | None = None) -> float | None:
        """Retrieve a float value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
        return self.get_float(*keys, default=default)

    @overload
    def get_str(self, *keys: str, default: None) -> str | None:
        ...
    @overload
    def get_str(self, *keys: str, default: str | _MISSING_CLS = _MISSING) -> str:
        ...
    def get_str(self, *keys: str, default: str | None | _MISSING_CLS = _MISSING) -> str | None:
        """Retrieve a string value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved string value or the default value if not found.
        """
        val = self._get(*keys, default=default, skip_none=True)
        return _handle_str(val, default, keys[0])

    def get_strn(self, *keys: str, default: str | None = None) -> str | None:
        """Retrieve a list of strings from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved list of strings or the default value if not found.
        """
        return self.get_str(*keys, default=default)

    def get_scopes(self, *keys: str) -> list[str]:
        """Retrieve a list of scopes from the configuration.

        :param keys: The keys of the scopes value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved list of scopes or the default value if not found.
        """
        val = self._get(*keys, default=None, skip_none=True)
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return Configuration.format_scopes(val)
        raise ValueError(f"Invalid scopes value: {val}")

    @staticmethod
    def format_scopes(scopes: str | list[str] | None) -> list[str]:
        """Format scopes into a list of strings. If scopes is a string, it will be split by whitespace. If scopes is None, an empty list is returned."""
        if scopes is None:
            return []
        if isinstance(scopes, str):
            lst = scopes.strip().split()
            return [s for s in lst if s]
        return scopes
        

class _Configurable(ABC):

    @classmethod
    def from_mapping(cls, _mapping: Mapping | None = None, **kwargs) -> Self:
        return cls.from_configuration(Configuration.from_mapping(_mapping, **kwargs))

    @classmethod
    @abstractmethod
    def _from_configuration(cls, config: Configuration) -> Self:...

    @classmethod
    @abstractmethod
    def from_configuration(cls, config: Configuration | Self) -> Self:
        if isinstance(config, cls):
            return config
        if isinstance(config, Configuration):
            return cls._from_configuration(config)
        raise TypeError(f"Cannot create {cls.__name__} from {type(config).__name__}")