# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Protocol,
    TypeGuard,
    TypeVar,
    overload,
)
from typing_extensions import Self

from ._configuration_protocol import _ConfigurationProtocol
from ._constants import _PATH_SEPARATOR
from ._coercion import (
    _handle_bool,
    _handle_int,
    _handle_float,
    _handle_str,
    _handle_str_list,
)
from ._utils import (
    _MissingType,
    _MISSING,
    _get,
    _get_with_path,
    _collect,
    _collect_with_paths,
    _is_missing,
    _resolve,
    _resolve_keys_arg,
)

T = TypeVar("T")
_ConfigurationProtocolT = TypeVar(
    "_ConfigurationProtocolT", bound=_ConfigurationProtocol
)


class Configuration(dict, _ConfigurationProtocol):
    """Dictionary-backed configuration with path lookup and typed conversion.

    Paths use ``::`` separators. Alternative paths are tried in the supplied
    order. Sections carry the matched source path for diagnostics.
    Construction makes a shallow copy; nested mutable values can remain shared.
    """

    def __init__(self, _original: Mapping | None = None, _base_path: str | None = None, **kwargs):
        """Initialize a Configuration instance.

        :param _original: The original mapping to initialize the configuration from.
        :param _base_path: The base path for resolving nested configuration keys.
        """
        if _original is not None and kwargs:
            raise ValueError("Cannot provide both '_original' and keyword arguments.")
        super().__init__(_original or kwargs)
        self._base_path = _base_path or ""
        
    @classmethod
    def from_mapping(
        cls, _mapping: Mapping | None = None, _base_path: str | None = None, **kwargs
    ) -> Configuration:
        """Create configuration, using keyword arguments as fallback values.

        An existing Configuration is reused unless defaults or a different
        diagnostic base path are supplied.
        """
        if (
            isinstance(_mapping, Configuration)
            and not kwargs
            and (_base_path is None or _base_path == _mapping._base_path)
        ):
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

    def _get_with_path(self, *_keys: str | list[str], default: Any = _MISSING, skip_none: bool = False) -> tuple[Any, list[str]]:
        """Return a value and its matched path segments, relative to this section."""
        keys = _resolve_keys_arg(*_keys)
        res, path = _get_with_path(self, *keys, default=_MISSING, skip_none=skip_none)
        if _is_missing(res):
            if _is_missing(default):
                raise KeyError(self._resolve_path(keys[0]))
            return default, path
        return res, path


    def _get(self, *_keys: str | list[str], default: Any = _MISSING, skip_none: bool = False) -> Any:
        """Return the first matched value, raising if absent and no default is given."""
        val, _ = self._get_with_path(*_keys, default=default, skip_none=skip_none)
        return val

    def get(self, key: str | list[str], default: Any = None, skip_none: bool = False) -> Any:
        """Retrieve a value from the configuration by key, returning the default if not found."""
        keys = _resolve_keys_arg(key)
        try:
            return self._get(*keys, default=default, skip_none=skip_none)
        except KeyError:
            return default

    def _get_typed(
        self,
        *_keys: str | list[str],
        cls: type[T],
        factory: Callable[[Any], T] | None = None,
        default: T | _MissingType = _MISSING,
    ) -> T:
        """Retrieve a value from the configuration by key, ensuring it is of the specified type.

        :param _keys: The keys to retrieve.
        :param cls: The expected type of the value.
        :param factory: An optional factory function to convert the value to the expected type.
        :param default: The default value to return if the key is not found or the value is not of the expected type.
        """

        keys = _resolve_keys_arg(*_keys)

        val, path = self._get_with_path(*keys)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])

        if isinstance(val, cls):
            return val
        if factory:
            new_val = factory(val)
            if isinstance(new_val, cls):
                return new_val
            else:
                raise TypeError(
                    f"Factory for key {name} did not return an instance of {cls.__name__}."
                )
        if not _is_missing(default):
            return default
        raise TypeError(
            f"Value for key {name} is not of type {cls.__name__} and could not be converted."
        )

    def has(self, *keys: str | list[str]) -> bool:
        """Check if the configuration contains the specified keys.

        :param keys: The keys to check.
        :return: True if the keys exist in the configuration, False otherwise.
        """
        resolved_keys = _resolve_keys_arg(*keys)
        try:
            self._get(*resolved_keys)
            return True
        except KeyError:
            return False

    @overload
    def get_section(
        self, *section: str | list[str], default: Configuration | _MissingType = _MISSING
    ) -> Configuration: ...
    @overload
    def get_section(self, *section: str | list[str], default: None) -> Configuration | None: ...
    def get_section(
        self, *section: str | list[str], default: Configuration | None | _MissingType = _MISSING
    ) -> Configuration | None:
        """Retrieve a section of the configuration, returning it as a Configuration object.

        :param section: Alternative section paths, tried in order.
        :param default: The default value to return if the section is not found.
        :return: The retrieved section as a Configuration object, or the default value if not found.
        :raises KeyError: If the section is not found and no default is provided.
        :raises TypeError: If the section is found but is not a mapping.
        """
        keys = _resolve_keys_arg(*section)
        val, path = self._get_with_path(*keys, default=default)
        if not path:
            return val
        base_path = self._resolve_path(_PATH_SEPARATOR.join(path))

        if isinstance(val, Mapping):
            return Configuration.from_mapping(
                val, _base_path=base_path
            )
        if val is None and not _is_missing(default):
            return default
        raise TypeError(f"Section {base_path} is not a mapping")

    def get_sections(self, *section: str) -> list[Configuration]:
        """Retrieve all subsections of the specified section as Configuration objects.

        :param section: The names of the nested sections to retrieve.
        :return: A list of Configuration objects representing the subsections.
        :raises TypeError: If the section is not a mapping.
        """
        map = _collect_with_paths(self, *section)

        if not map:
            return []

        for base_path, v in map.items():
            if not isinstance(v, Mapping):
                raise TypeError(
                    f"Section {self._resolve_path(base_path)} is not a mapping"
                )

        return [
            Configuration.from_mapping(v, _base_path=self._resolve_path(base_path))
            for base_path, v in map.items()
        ]

    # @overload
    # def get_typed(
    #     self,
    #     _type: type[T],
    #     *_keys: str | list[str],
    #     factory: Callable[[Mapping], T] | None = None,
    #     default: T | _MissingType = _MISSING,
    # ) -> T: ...
    # @overload
    # def get_typed(
    #     self,
    #     _type: type[T],
    #     *_keys: str | list[str],
    #     factory: Callable[[Mapping], T],
    #     default: None,
    # ) -> T | None: ...
    # @overload
    # def get_typed(
    #     self,
    #     _type: type[_ConfigurationProtocolT],
    #     *_keys: str | list[str],
    #     factory: None = None,
    #     default: _ConfigurationProtocolT | _MissingType,
    # ) -> _ConfigurationProtocolT: ...
    # @overload
    # def get_typed(
    #     self,
    #     _type: type[_ConfigurationProtocolT],
    #     *_keys: str | list[str],
    #     factory: None = None,
    #     default: _ConfigurationProtocolT | None | _MissingType = _MISSING,
    # ) -> _ConfigurationProtocolT | None: ...
    # def get_typed(
    #     self,
    #     _type: type[T],
    #     *_keys: str | list[str],
    #     factory: Callable[[Mapping], T] | None = None,
    #     default: T | None | _MissingType = _MISSING,
    # ) -> T | None:
    #     """Retrieve a typed value from the configuration, converting it to the specified class if necessary.

    #     :param _type: The expected type of the section.
    #     :param key: The key of the section to retrieve. If None, uses the type name as the key.
    #     :param factory: The factory to convert the section with, if necessary.
    #     :param default: The default value to return if the section is not found.
    #     :return: The retrieved section as an instance of the specified type, or the default value if not found.
    #     :raises TypeError: If the return type of the class is not a subclass of the expected type.
    #     """
    #     keys = _resolve_keys_arg(*_keys) if _keys else [_type.__name__]
    #     val = self._get(*keys, default=default)

    #     if not isinstance(val, Mapping):
    #         raise TypeError(
    #             f"Section {keys[0]} is not a mapping. This may be supported in the future."
    #         )

    #     if not factory:
    #         if isinstance(_type, _ConfigurationProtocol):
    #             return _type.from_mapping(val)
    #         raise ValueError(
    #             f"Type {_type} is not a subclass of _ConfigurationProtocol and no factory was provided"
    #         )

    #     return factory(val)

    @overload
    def get_bool(self, *_keys: str | list[str], default: bool | _MissingType = _MISSING) -> bool:
        ...
    @overload
    def get_bool(self, *_keys: str | list[str], default: None = None) -> bool | None:
        ...
    def get_bool(self, *_keys: str | list[str], default: bool | None | _MissingType = _MISSING) -> bool | None:
        """Retrieve a boolean value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=default, skip_none=True)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        return _handle_bool(val, default, name)

    def get_booln(self, *_keys: str | list[str], default: bool | None = None) -> bool | None:
        """Retrieve a boolean value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
        """
        return self.get_bool(*_keys, default=default)

    @overload
    def get_int(self, *_keys: str | list[str], default: None = None) -> int | None:
        ...
    @overload
    def get_int(self, *_keys: str | list[str], default: int | _MissingType = _MISSING) -> int:
        ...
    def get_int(self, *_keys: str | list[str], default: int | None | _MissingType = _MISSING) -> int | None:
        """Retrieve an integer value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=default, skip_none=True)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        return _handle_int(val, default, name)

    def get_intn(self, *_keys: str | list[str], default: int | None = None) -> int | None:
        """Retrieve an integer value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        return self.get_int(*_keys, default=default)

    @overload
    def get_float(self, *_keys: str | list[str], default: None = None) -> float | None:
        ...
    @overload
    def get_float(self, *_keys: str | list[str], default: float | _MissingType = _MISSING) -> float:
        ...
    def get_float(self, *_keys: str | list[str], default: float | None | _MissingType = _MISSING) -> float | None:
        """Retrieve a float value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=default, skip_none=True)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        return _handle_float(val, default, name)

    def get_floatn(self, *_keys: str | list[str], default: float | None = None) -> float | None:
        """Retrieve a float value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
        return self.get_float(*_keys, default=default)

    @overload
    def get_str(self, *_keys: str | list[str], default: None) -> str | None:
        ...
    @overload
    def get_str(self, *_keys: str | list[str], default: str | _MissingType = _MISSING) -> str:
        ...
    def get_str(self, *_keys: str | list[str], default: str | None | _MissingType = _MISSING) -> str | None:
        """Retrieve a string value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved string value or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=default, skip_none=True)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        return _handle_str(val, default, name)

    def get_strn(self, *_keys: str | list[str], default: str | None = None):
        """Retrieve a string, allowing None as the default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved string or the default value if not found.
        """
        return self.get_str(*_keys, default=default)

    def get_str_list(self, *_keys: str | list[str], default: list[str] | None = None) -> list[str]:
        """Retrieve a list of strings from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved list of strings or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=default, skip_none=True)
        if val is None:
            if default is None:
                return []
            return default
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        return _handle_str_list(val, default, name)

    def get_items(self, *_keys: str | list[str], default: dict | None = None) -> Iterable[tuple[Any, Any]]:
        """Retrieve items from a dictionary in the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved items as a list of key-value tuples or the default value if not found.
        """
        keys = _resolve_keys_arg(*_keys)
        base = _get(self, *keys, default=default)
        if isinstance(base, Mapping):
            return base.items()
        elif isinstance(base, list):
            return enumerate(base)
        return []

    def collect(self, *_keys: str | list[str]) -> list[Any]:
        keys = _resolve_keys_arg(*_keys)
        return _collect(self, *keys)

    def collect_str(self, *_keys: str | list[str]) -> list[str]:
        keys = _resolve_keys_arg(*_keys)
        vals = _collect(self, *keys)
        vals = [ _handle_str(v, None, keys[0]) for v in vals if v is not None ]
        return [ v for v in vals if v is not None ]

    def get_scopes(self, *_keys: str | list[str]) -> list[str]:
        """Retrieve a list of scopes from the configuration.

        :param keys: The keys of the scopes value to retrieve.
        :return: The scopes as a list, or an empty list if absent.
        """
        keys = _resolve_keys_arg(*_keys)
        val, path = self._get_with_path(*keys, default=None, skip_none=True)
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return Configuration.format_scopes(val)
        name = self._resolve_path(_PATH_SEPARATOR.join(path) or keys[0])
        raise ValueError(f"Invalid scopes value for {name}")

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
    def from_configuration(cls, config: Configuration | Self) -> Self:
        if isinstance(config, cls):
            return config
        if isinstance(config, Configuration):
            return cls._from_configuration(config)
        raise TypeError(f"Cannot create {cls.__name__} from {type(config).__name__}")