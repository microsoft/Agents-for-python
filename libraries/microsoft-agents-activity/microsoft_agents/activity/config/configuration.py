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
    """Dictionary-backed configuration with path lookup and typed conversion.

    Use string keys for direct lookup and lists of segments for nested lookup.
    Matching is exact unless an internal path object supplies a different
    case/underscore policy. Collection methods accept explicit wildcard segments.

    Construction copies the outer mapping and recursively wraps plain nested
    mappings and sequences. Existing query wrappers can remain shared.
    Source normalization and merging are handled by ``resolve``. Extracted
    sections carry source paths for diagnostics.

    Plain mappings are scoped by default. Root configurations, such as those
    returned by ``load_configuration_from_env``, let settings binders locate
    their sections within the application configuration. Root identity is
    explicit metadata, independent of the diagnostic base path.
    """

    def __init__(
        self,
        original: Mapping | None = None,
        _base_path: str | Sequence[str] | None = None,
    ):
        """Wrap a mapping without expanding key names or coercing values.

        :param original: The original mapping to initialize the configuration from.
        :param _base_path: Diagnostic path as a string or sequence of strings.
            An omitted or empty path inherits the original object's base path,
            if present.
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
        """Source path used in diagnostics."""
        return self._base_path

    @property
    def key(self) -> str:
        """Last source-path segment, or an empty string when no path is set."""
        if not self._key:
            self._key = (
                self._base_path.rsplit(_PATH_SEPARATOR, maxsplit=1)[-1]
                if self._base_path
                else ""
            )
        return self._key

    @classmethod
    def resolve(
        cls,
        primary: Mapping | None = None,
        defaults: Mapping | None = None,
        *,
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
        return Configuration(resolved, _base_path=_base_path)

    @classmethod
    def from_config(
        cls, base: Mapping | None, *, _base_path: str | None = None
    ) -> Configuration:
        """Create a wrapper, retaining mapping metadata and diagnostic source path.

        ``None`` creates empty scoped configuration. Key spelling is preserved.
        A nonempty ``_base_path`` rebases diagnostics without modifying the input.
        Existing nested query wrappers may remain shared.
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
        """Return the first value matching one path, or ``default`` if absent.

        Use a string key for direct lookup or a list of segments for nested
        lookup. ``skip_none=True`` continues searching matching candidates
        until a non-``None`` value is found. Wildcard paths are not accepted.
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
        """Retrieve a section of the configuration, returning it as a Configuration object.

        :param section: A key or path to a mapping.
        :param default: Returned if the section is absent, or its value is
            ``None``. Without a default, absence raises ``KeyError``.
        :return: The retrieved section as a Configuration object, or the default value if not found.
        :raises KeyError: If the section is not found and no default is provided.
        :raises TypeError: If the section is found but is not a mapping.
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
        """Retrieve all subsections of the specified section as Configuration objects.

        :param section: A path, optionally containing internal wildcard segments.
        :return: A list of Configuration objects representing the subsections.
        :raises TypeError: If a matched value is not a mapping.
        :raises KeyError: If multiple matches have the same final source key.
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
        """Convert a matched value to a bool, skipping ``None`` candidates.

        Strings accept ``true/1`` and ``false/0``, ignoring case and whitespace.
        Missing or blank values return an explicit default; without one they
        raise ``KeyError`` or ``ValueError``. Invalid nonempty values raise
        ``ValueError`` even when a default is supplied.

        :param path: A key or path.
        :param default: Fallback for missing, ``None``, or blank values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_bool(val, default, self._resolve_path(found_path or path))

    def get_booln(self, path: _PathProxy, default: bool | None = None) -> bool | None:
        """Call ``get_bool`` with a nullable default, ``None`` unless supplied."""
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
        """Convert a matched value to an int, skipping ``None`` candidates.

        Decimal and float-form strings are accepted; float-form values are
        truncated. Blank values and bools use an explicit default. Missing
        values without a default raise ``KeyError``; unset or invalid values
        can raise ``ValueError``.

        :param path: A key or path.
        :param default: Fallback for missing or unset values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_int(val, default, self._resolve_path(found_path or path))

    def get_intn(self, path: _PathProxy, default: int | None = None) -> int | None:
        """Call ``get_int`` with a nullable default, ``None`` unless supplied."""
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
        """Convert a matched value to a float, skipping ``None`` candidates.

        Blank values and bools use an explicit default. Missing values without
        a default raise ``KeyError``; unset or invalid values can raise
        ``ValueError``.

        :param path: A key or path.
        :param default: Fallback for missing or unset values.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_float(val, default, self._resolve_path(found_path or path))

    def get_floatn(
        self, path: _PathProxy, default: float | None = None
    ) -> float | None:
        """Call ``get_float`` with a nullable default, ``None`` unless supplied."""
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
        """Convert a matched value to a string, skipping ``None`` candidates.

        Existing strings, including empty strings, are preserved. Other values
        use ``str()``. Missing values without a default raise ``KeyError``.

        :param path: A key or path.
        :param default: Fallback for a missing or ``None`` value.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_str(val, default, self._resolve_path(found_path or path))

    def get_strn(self, path: _PathProxy, default: str | None = None):
        """Call ``get_str`` with a nullable default, ``None`` unless supplied."""
        return self.get_str(path, default=default)

    def get_str_list(
        self, path: _PathProxy, default: list[str] | None = None
    ) -> list[str]:
        """Read a string list, skipping ``None`` matches and list elements.

        Sequence elements are converted to strings. Scalar text is split on
        commas when present, otherwise on whitespace. Use ``get_scopes`` when
        both separators must be handled together. Mapping values are rejected.

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
        """Return mapping entries or enumerated sequence elements at one path.

        :param path: A key or path.
        :param default: Fallback value inspected when no match exists.
        :return: A mapping's items view, an enumeration of a non-text sequence,
            or an empty list for other values.
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
        """Collect all matching leaves, including ``None``, in traversal order.

        Use explicit internal wildcard segments to enumerate mapping keys.
        Matching leaves must have distinct final source keys, or ``KeyError``
        is raised. Sequence traversal requires a numeric segment.
        """
        return _collect(self, _Path.create(path))

    def collect_str(self, _path: _PathProxy) -> list[str]:
        """Collect matches as strings, omitting ``None`` values."""
        path = _Path.create(_path)
        vals = _collect(self, path)
        vals = [_handle_str(v, None, path) for v in vals if v is not None]
        return [v for v in vals if v is not None]

    def get_scopes(self, _path: _PathProxy) -> list[str]:
        """Retrieve a list of scopes from the configuration.

        Strings split on both commas and whitespace; mutable sequences are
        copied without coercing their elements. Other value types are rejected.

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
        """Split strings on commas and whitespace, copy lists, or map None to []."""
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
    """Bind typed settings from a Configuration or reuse an already-bound object."""

    @classmethod
    @abstractmethod
    def _from_config(cls, config: Configuration) -> Self: ...

    @classmethod
    def from_config(cls, config: Mapping | Self | None) -> Self:
        """Bind a mapping or Configuration, reuse settings, or bind defaults.

        Plain mappings are wrapped with their key names preserved.
        Existing instances of this settings class are returned unchanged.
        ``None`` binds an empty scoped Configuration.

        :raises TypeError: If config is not a supported input type.
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
    """Bind settings from either application-level or scoped configuration.

    Subclasses implement root and scoped binding separately. Dispatch uses root
    metadata stored in the mapping.
    A root binder locates its own section, while a scoped binder reads fields
    directly. Passing None uses the scoped binder with empty configuration.
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
