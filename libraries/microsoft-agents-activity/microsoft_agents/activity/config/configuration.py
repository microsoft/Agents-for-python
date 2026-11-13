# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    TypeVar,
    Sequence,
    overload,
)
from typing_extensions import Self

from ._protocol import _MappingConfigurable
from ._constants import _PATH_SEPARATOR
from ._engine._resolve import _default_path_transformer, _resolve
from ._engine._coercion import (
    _handle_bool,
    _handle_int,
    _handle_float,
    _handle_str,
    _handle_str_list,
)
from ._engine import (
    _Path,
    _PathProxy,
    _MissingType,
    _MISSING,
    _get,
    _get_with_path,
    _collect,
    _collect_with_paths,
    _is_missing,
    _QueryDict,
)
from ._metadata import (
    _RootConfigMetadata,
)

T = TypeVar("T")
_MappingConfigurableT = TypeVar("_MappingConfigurableT", bound=_MappingConfigurable)


def _norm_path_transform(parts: list[str]) -> _Path:
    return _default_path_transformer([part.lower() for part in parts])


class Configuration(_QueryDict, _MappingConfigurable):
    """Read settings from nested dictionaries and lists, with type conversion.

    Pass a dictionary, then use a string for one key or a list of keys for a
    nested value. Values keep their original types until you request a
    conversion with a method such as ``get_int`` or ``get_bool``::

        >>> from microsoft_agents.activity.config import Configuration
        >>> config = Configuration({
        ...     "service": {"timeout": "30", "enabled": "false"},
        ...     "servers": [{"name": "first"}, {"name": "last"}],
        ... })
        >>> config.get(["service", "timeout"])
        '30'
        >>> config.get_int(["service", "timeout"])
        30
        >>> config.get_bool(["service", "enabled"])
        False
        >>> config.get("missing", default="fallback")
        'fallback'

    Key matching is case-sensitive: ``"service"`` and ``"Service"`` are different
    keys. Use a list such as ``["service", "timeout"]`` for nested lookup, not
    ``"service::timeout"``. List positions require integers; negative indexes
    count from the end::

        >>> config.get(["servers", 0, "name"])
        'first'
        >>> config.get(["servers", -1, "name"])
        'last'
        >>> config.get(["servers", "0", "name"], default="not found")
        'not found'

    You can also update values using dictionary operations::

        >>> config["service"]["timeout"] = "45"
        >>> config.get_int(["service", "timeout"])
        45

    Use ``get_section`` to work with one nested dictionary, and ``wildcard()``
    with collection methods to read values from several dictionaries.
    The string ``"*"`` is a literal key, not a wildcard.

    For environment-style names such as ``SERVICE__TIMEOUT``, use
    ``load_configuration_from_env`` instead. That function also prepares the
    result for SDK APIs that accept the full application configuration.

    Construction copies ordinary dictionaries and wraps nested dictionaries and
    lists. Wrapping another Configuration is not a deep copy: nested containers
    may be shared.
    """

    def __init__(
        self,
        original: Mapping | None = None,
        _base_path: str | Sequence[str] | None = None,
    ):
        """Create configuration from a dictionary, keeping key names and values.

        :param original: Settings to read, or ``None`` for empty configuration.
            Environment-style names are not expanded here; use
            ``load_configuration_from_env`` when that is needed.
        :param _base_path: Internal prefix used to identify settings in error
            messages. Normally supplied automatically by ``get_section``.
        """
        super().__init__(original or {})
        if not isinstance(_base_path, str) and _base_path is not None:
            _base_path = "::".join(_base_path)
        self._base_path = _base_path or getattr(original, "_base_path", "")
        if not isinstance(self._base_path, str):
            raise TypeError(f"Unsupported type for base path: {type(self._base_path)}")
        self._key = None

    @property
    def base_path(self) -> str:
        """Location of this section in the original configuration.

        For example, ``config.get_section("service").base_path`` is ``"service"``.
        Error messages include this location to help identify the setting.
        """
        return self._base_path

    @property
    def key(self) -> str:
        """Name of this section, such as ``"service"`` after ``get_section("service")``.

        Returns an empty string for configuration without a section path.
        """
        if not self._key:
            self._key = (
                self._base_path.rsplit(_PATH_SEPARATOR, maxsplit=1)[-1]
                if self._base_path
                else ""
            )
        return self._key

    @classmethod
    def _resolve(
        cls,
        primary: Mapping | None = None,
        defaults: Mapping | None = None,
        *,
        _ensure_root_config: bool = True,
        _base_path: str | None = None,
    ) -> Configuration:
        """Normalize source names and merge with primary values taking precedence.

        Source names are lowercased, and ``__`` or ``::`` separators expand into
        nested sections. Primary lists replace default lists. Neither input's
        containers are modified, and this method does not apply logging configuration.

        :param primary: Values that override defaults.
        :param defaults: Optional fallback values.
        :param _base_path: Diagnostic source path for the result.
        """
        resolved = _resolve(
            primary or {}, defaults or {}, path_transformer=_norm_path_transform
        )
        config = Configuration(resolved, _base_path=_base_path)
        if _ensure_root_config:
            _RootConfigMetadata.set(config, True)
        return config

    @classmethod
    def from_config(
        cls, base: Mapping | None, *, _base_path: str | None = None
    ) -> Configuration:
        """Create Configuration from a dictionary or another Configuration.

        ``None`` creates empty configuration. Existing key names and section
        locations are preserved. Nested values may be shared when copying
        another Configuration.

        :param base: Settings to wrap.
        :param _base_path: Internal override for the section location shown in
            error messages; it does not change the input.
        """
        _base_path = _base_path or getattr(base, "_base_path", None)
        return Configuration(base, _base_path=_base_path)

    def _resolve_path(self, path: str | _Path) -> str:
        """Resolve a configuration path by combining the base path and the key."""
        if not self._base_path:
            return str(path)
        return f"{self._base_path}::{str(path)}"

    def _get_with_path(
        self, _path: _PathProxy, default: Any = _MISSING, skip_none: bool = False
    ) -> tuple[Any, _Path | None]:
        """Return a value and its matched path segments, relative to this section."""
        path = _Path.create(_path)
        res, found_path = _get_with_path(
            self, path, default=default, skip_none=skip_none
        )
        if _is_missing(res):
            if _is_missing(default):
                raise KeyError(path._prepend_to_str(self._base_path))
            return default, None
        return res, found_path

    def _get(
        self, path: _PathProxy, default: Any = _MISSING, skip_none: bool = False
    ) -> Any:
        """Return the first matched value, raising if absent and no default is given."""
        val = _get(self, path, default=default, skip_none=skip_none)
        if _is_missing(val):
            if _is_missing(default):
                raise KeyError(path._prepend_to_str(self._base_path))
            return default
        return val

    def get(
        self, key: _PathProxy, default: Any = None, *, skip_none: bool = False
    ) -> Any:
        """Read a value without changing its type, or return a default if missing.

        Use a string for one key or a list of keys and integer indexes for a
        nested value. A stored ``None`` is returned unchanged unless
        ``skip_none=True``, which treats it as missing. To read multiple values
        using ``wildcard()``, use ``collect`` instead.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"service": {"timeout": "30", "note": None}})
            >>> config.get(["service", "timeout"])
            '30'
            >>> config.get(["service", "missing"], default="fallback")
            'fallback'
            >>> config.get(["service", "note"], default="fallback") is None
            True
            >>> config.get(["service", "note"], default="fallback", skip_none=True)
            'fallback'
        """
        path = _Path.create(key)
        try:
            return self._get(path, default=default, skip_none=skip_none)
        except KeyError:
            return default

    @overload
    def get_section(
        self,
        section: _PathProxy,
        default: Configuration | _MissingType = _MISSING,
    ) -> Configuration: ...
    @overload
    def get_section(
        self, section: _PathProxy, default: None
    ) -> Configuration | None: ...
    def get_section(
        self,
        section: _PathProxy,
        default: Configuration | None | _MissingType = _MISSING,
    ) -> Configuration | None:
        """Read one nested dictionary as Configuration.

        Lookups on the returned object start inside that section. Its
        ``base_path`` records the section's location for error messages::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"service": {"timeout": "30"}})
            >>> service = config.get_section("service")
            >>> service.get_int("timeout")
            30
            >>> service.base_path
            'service'
            >>> service.key
            'service'
            >>> config.get_section("missing", default=None) is None
            True

        :param section: One key or a list of keys leading to a dictionary.
        :param default: Value to return if the section is missing or ``None``.
        :raises KeyError: If the section is missing and no default is provided.
        :raises TypeError: If the value is not a dictionary. A stored ``None``
            also raises this error when no default is provided.
        """
        path = _Path.create(section)
        val, found_path = self._get_with_path(path, default=default)
        if not found_path:
            return val
        base_path = self._resolve_path(found_path)

        if isinstance(val, Mapping):
            return Configuration.from_config(val, _base_path=base_path)
        if val is None and not _is_missing(default):
            return default
        raise TypeError(f"Section {base_path} is not a mapping")

    def get_sections(self, section: _PathProxy) -> list[Configuration]:
        """Read several nested dictionaries as a list of Configuration objects.

        Put ``wildcard()`` in the path to visit every key at that dictionary
        level. If nothing matches, return an empty list::

            >>> from microsoft_agents.activity.config import Configuration, wildcard
            >>> config = Configuration({
            ...     "services": {
            ...         "first": {"timeout": "10"},
            ...         "second": {"timeout": "20"},
            ...     },
            ... })
            >>> sections = config.get_sections(["services", wildcard()])
            >>> [section.key for section in sections]
            ['first', 'second']
            >>> [section.get_int("timeout") for section in sections]
            [10, 20]

        :param section: One key or a list of keys, indexes, and wildcards.
        :raises TypeError: If any matched value is not a dictionary.
        """
        path = _Path.create(section)
        map = _collect_with_paths(self, path)

        if not map:
            return []

        for entry in map.values():
            if not isinstance(entry.value, Mapping):
                raise TypeError(
                    f"Section {self._resolve_path(entry.path)} is not a mapping"
                )

        return [
            Configuration.from_config(
                entry.value, _base_path=self._resolve_path(entry.path)
            )
            for entry in map.values()
        ]

    @overload
    def get_bool(
        self, path: _PathProxy, default: bool | _MissingType = _MISSING
    ) -> bool: ...
    @overload
    def get_bool(self, path: _PathProxy, default: None = None) -> bool | None: ...
    def get_bool(
        self, path: _PathProxy, default: bool | None | _MissingType = _MISSING
    ) -> bool | None:
        """Read a setting as a boolean.

        Strings accept ``"true"``/``"1"`` and ``"false"``/``"0"``, ignoring case
        and surrounding whitespace. Unlike ``bool("false")``, this correctly
        reads the string ``"false"`` as False.
        Missing or blank values return an explicit default; without one they
        raise ``KeyError`` or ``ValueError``. Invalid nonempty values raise
        ``ValueError`` even when a default is supplied.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"enabled": "false"})
            >>> config.get_bool("enabled")
            False
            >>> config.get_bool("missing", default=True)
            True

        :param path: A key or path.
        :param default: Fallback for missing, ``None``, or blank values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_bool(val, default, self._resolve_path(found_path or path))

    def get_booln(self, path: _PathProxy, default: bool | None = None) -> bool | None:
        """Read a boolean, returning ``None`` for missing or blank settings by default.

        Like ``get_bool``, invalid nonempty values still raise ``ValueError``.
        """
        return self.get_bool(path, default=default)

    @overload
    def get_int(self, path: _PathProxy, default: None = None) -> int | None: ...
    @overload
    def get_int(
        self, path: _PathProxy, default: int | _MissingType = _MISSING
    ) -> int: ...
    def get_int(
        self, path: _PathProxy, default: int | None | _MissingType = _MISSING
    ) -> int | None:
        """Read a setting as an integer.

        Accept numeric strings such as ``"5"`` and ``"5.9"``; fractional parts
        are discarded. Missing, ``None``, blank, and boolean values use the
        default when one is supplied. Without a default, missing values raise
        ``KeyError`` and blank or boolean values raise ``ValueError``.
        Invalid nonempty values raise ``ValueError`` even with a default.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"retries": "3", "limit": "5.9"})
            >>> config.get_int("retries")
            3
            >>> config.get_int("limit")
            5
            >>> config.get_int("missing", default=10)
            10

        :param path: A key or path.
        :param default: Fallback for missing or unset values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_int(val, default, self._resolve_path(found_path or path))

    def get_intn(self, path: _PathProxy, default: int | None = None) -> int | None:
        """Read an integer, returning ``None`` for missing or blank settings by default.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration()
            >>> config.get_intn("optional_limit") is None
            True
            >>> config.get_intn("optional_limit", default=10)
            10
        """
        return self.get_int(path, default=default)

    @overload
    def get_float(self, path: _PathProxy, default: None = None) -> float | None: ...
    @overload
    def get_float(
        self, path: _PathProxy, default: float | _MissingType = _MISSING
    ) -> float: ...
    def get_float(
        self, path: _PathProxy, default: float | None | _MissingType = _MISSING
    ) -> float | None:
        """Read a setting as a floating-point number.

        Missing, ``None``, blank, and boolean values use the default when one is
        supplied. Without a default, missing values raise ``KeyError`` and
        blank or boolean values raise ``ValueError``. Invalid nonempty values
        raise ``ValueError`` even with a default.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"delay": "0.5"})
            >>> config.get_float("delay")
            0.5
            >>> config.get_float("missing", default=1.0)
            1.0

        :param path: A key or path.
        :param default: Fallback for missing or unset values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_float(val, default, self._resolve_path(found_path or path))

    def get_floatn(
        self, path: _PathProxy, default: float | None = None
    ) -> float | None:
        """Read a float, returning ``None`` for missing or blank settings by default."""
        return self.get_float(path, default=default)

    @overload
    def get_str(self, path: _PathProxy, default: None) -> str | None: ...
    @overload
    def get_str(
        self, path: _PathProxy, default: str | _MissingType = _MISSING
    ) -> str: ...
    def get_str(
        self, path: _PathProxy, default: str | None | _MissingType = _MISSING
    ) -> str | None:
        """Read a setting as a string.

        Existing strings, including empty strings, are preserved. Other values
        are converted with ``str()``. Missing or ``None`` values use the default,
        or raise ``KeyError`` if no default was supplied.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"port": 3978, "label": ""})
            >>> config.get_str("port")
            '3978'
            >>> config.get_str("label", default="agent")
            ''

        :param path: A key or path.
        :param default: Fallback for a missing or ``None`` value.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_str(val, default, self._resolve_path(found_path or path))

    def get_strn(self, path: _PathProxy, default: str | None = None):
        """Read a string, returning ``None`` for missing settings by default."""
        return self.get_str(path, default=default)

    def get_str_list(
        self, path: _PathProxy, default: list[str] | None = None
    ) -> list[str]:
        """Read a list of strings from a list or a text setting.

        List elements are converted to strings and ``None`` elements are
        omitted. Text is split on commas if any are present, otherwise on
        whitespace. Use ``get_scopes`` to split on both at once.
        Dictionaries are not accepted.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"roles": "read, write", "ids": [1, None, 2]})
            >>> config.get_str_list("roles")
            ['read', 'write']
            >>> config.get_str_list("ids")
            ['1', '2']
            >>> config.get_str_list("missing")
            []

        :param path: A key or path.
        :param default: Fallback list; missing values return ``[]`` if omitted.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        if val is None:
            if default is None:
                return []
            return default
        if isinstance(val, MutableSequence):
            return _handle_str_list(
                list(val), default, self._resolve_path(found_path or path)
            )
        elif isinstance(val, Mapping):
            raise ValueError(
                f"Invalid list value for {self._resolve_path(found_path or path)}"
            )
        elif not isinstance(val, Mapping):
            before_split = _handle_str(
                val, None, self._resolve_path(found_path or path)
            )
            if before_split is None:
                return default if default is not None else []
            if "," in before_split:
                return [s.strip() for s in before_split.split(",")]
            return [s.strip() for s in before_split.strip().split()]

    def get_items(
        self, path: _PathProxy, default: dict | None = None
    ) -> Iterable[tuple[Any, Any]]:
        """Read a dictionary's key/value pairs or a list's index/value pairs.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"labels": {"name": "agent"}, "ports": [3978]})
            >>> list(config.get_items("labels"))
            [('name', 'agent')]
            >>> list(config.get_items("ports"))
            [(0, 3978)]

        :param path: A key or path.
        :param default: Dictionary to use if the setting is missing.
        :return: Iterable of pairs, or an empty list for other value types.
        """
        base = _get(self, path, default=default)
        if isinstance(base, Mapping):
            return base.items()
        elif isinstance(base, Sequence) and not isinstance(
            base, (str, bytes, bytearray)
        ):
            return enumerate(base)
        return []

    def collect(self, path: _PathProxy) -> list[Any]:
        """Read all values matching a path, including ``None`` values.

        Use ``wildcard()`` to match every key at one dictionary level. Results
        follow dictionary insertion order, and a missing path returns ``[]``.
        A wildcard does not enumerate list positions; use an integer index
        for those. The string ``"*"`` selects a literal key.

        Example::

            >>> from microsoft_agents.activity.config import Configuration, wildcard
            >>> config = Configuration({
            ...     "services": {
            ...         "first": {"timeout": 10},
            ...         "second": {"timeout": 20},
            ...     },
            ... })
            >>> config.collect(["services", wildcard(), "timeout"])
            [10, 20]
            >>> config.collect(["missing", wildcard()])
            []
        """
        return _collect(self, _Path.create(path))

    def collect_str(self, _path: _PathProxy) -> list[str]:
        """Like ``collect``, but convert results to strings and omit ``None``.

        Example::

            >>> from microsoft_agents.activity.config import Configuration, wildcard
            >>> config = Configuration({"values": {"first": 1, "second": None}})
            >>> config.collect_str(["values", wildcard()])
            ['1']
        """
        path = _Path.create(_path)
        vals = _collect(self, path)
        vals = [_handle_str(v, None, path) for v in vals if v is not None]
        return [v for v in vals if v is not None]

    def get_scopes(self, _path: _PathProxy) -> list[str]:
        """Read OAuth scopes as a list.

        Text can separate scopes with commas, whitespace, or both. A configured
        list is copied without changing its elements. Missing or ``None`` values
        return ``[]``; other value types raise ``ValueError``.

        Example::

            >>> from microsoft_agents.activity.config import Configuration
            >>> config = Configuration({"scopes": "User.Read, Mail.Read Files.Read"})
            >>> config.get_scopes("scopes")
            ['User.Read', 'Mail.Read', 'Files.Read']

        :param _path: A key or path.
        :return: The scopes as a list, or an empty list if absent.
        """
        path = _Path.create(_path)
        val = self._get(path, default=None, skip_none=True)
        if val is None:
            return []
        if isinstance(val, MutableSequence):
            return list(val)
        if isinstance(val, str):
            return Configuration.format_scopes(val)
        raise ValueError(f"Invalid scopes value for {self._resolve_path(path)}")

    @staticmethod
    def format_scopes(scopes: str | list[str] | None) -> list[str]:
        """Convert scope text or a scope list to a list, without reading a setting.

        Split text on commas and whitespace, copy existing lists, and return
        ``[]`` for ``None``.
        """
        if scopes is None:
            return []
        if isinstance(scopes, str):
            scopes = scopes.replace(",", " ")
            lst = scopes.strip().split()
            return [s for s in lst if s]
        return list(scopes)

    @staticmethod
    def _from_config_or_kwargs(
        primary_config: Mapping | None,
        kwargs: MutableMapping,
        *,
        ensure_root_config: bool = False,
    ) -> Configuration:
        """Prefer explicit config; otherwise wrap deprecated root keyword data.

        Keyword values are not merged when ``primary_config`` is supplied.
        ``ensure_root_config`` marks only the keyword fallback as root input.
        """
        if primary_config is None:
            if ensure_root_config:
                _RootConfigMetadata.set(kwargs, True)
            return Configuration.from_config(kwargs)
        return Configuration.from_config(primary_config)


class _Configurable(ABC):
    """Shared ``from_config`` helper for SDK settings classes."""

    @classmethod
    @abstractmethod
    def _from_config(cls, config: Configuration) -> Self: ...

    @classmethod
    def from_config(cls, config: Mapping | Self | None) -> Self:
        """Create settings from a dictionary or Configuration.

        Passing an existing instance of this settings class returns it
        unchanged. Pass ``None`` to use the class's default settings; validation
        still applies if the class requires particular values.

        :param config: A dictionary, Configuration, existing settings object,
            or ``None``.
        :raises TypeError: If the input is not one of those types.
        """

        if isinstance(config, cls):
            return config

        if config is None:
            config = Configuration()
        elif isinstance(config, Mapping) and not isinstance(config, Configuration):
            config = Configuration.from_config(config)
        if isinstance(config, Configuration):
            return cls._from_config(config)
        raise TypeError(f"Cannot create {cls.__name__} from {type(config).__name__}")


class _RootConfigurable(_Configurable, ABC):
    """Support both a full application configuration and one component's settings.

    Configuration from ``load_configuration_from_env`` represents the full
    application, so each subclass finds its own section. An ordinary dictionary
    or Configuration is read as that component's settings directly.
    Passing ``None`` reads an empty settings dictionary.
    """

    @classmethod
    def _from_config(cls, config: Configuration) -> Self:
        if _RootConfigMetadata.get(config):
            return cls._from_root_configuration(config)
        return cls._from_scoped_configuration(config)

    @classmethod
    @abstractmethod
    def _from_scoped_configuration(cls, config: Configuration) -> Self: ...

    @classmethod
    @abstractmethod
    def _from_root_configuration(cls, config: Configuration) -> Self: ...
