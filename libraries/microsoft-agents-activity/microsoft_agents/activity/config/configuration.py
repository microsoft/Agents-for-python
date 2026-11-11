# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    Iterable,
    Mapping,
    MutableMapping,
    TypeVar,
    Sequence,
    overload,
)
from typing_extensions import Self

from ._protocol import _MappingConfigurable
from ._constants import _PATH_SEPARATOR
from ._engine._resolve import _resolve
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
    _parse_env_var_name,
)
from ._metadata import (
    _RootConfigMetadata,
)

T = TypeVar("T")
_MappingConfigurableT = TypeVar(
    "_MappingConfigurableT", bound=_MappingConfigurable
)

def _norm_path_transform(path: str) -> str:
    return _parse_env_var_name(path).lower()

class Configuration(dict, _MappingConfigurable):
    """Dictionary-backed configuration with path lookup and typed conversion.

    Paths use ``::`` separators. Alternative paths are tried in the supplied
    order. Sections carry the matched source path for diagnostics.
    Construction makes a shallow copy; nested mutable values can remain shared.

    Plain mappings are scoped by default. Root configurations, such as those
    returned by ``load_configuration_from_env``, let settings binders locate
    their sections within the application configuration. Root identity is
    explicit metadata, independent of the diagnostic base path.
    """

    def __init__(
        self,
        original: Mapping | None = None,
        _base_path: str | Sequence[str] | None = None
    ):
        """Initialize a Configuration instance.

        :param original: The original mapping to initialize the configuration from.
        :param _base_path: Source path used in diagnostics; defaults to an empty
            path, even when copying another Configuration.
        :param kwargs: Configuration entries when no original mapping is supplied.
        :raises ValueError: If both original and keyword entries are supplied.
        """
        super().__init__(original or {})
        if not isinstance(_base_path, str) and _base_path is not None:
            _base_path = "::".join(_base_path)
        self._base_path = _base_path or getattr(original, "_base_path", "")
        self._key = None

    @property
    def base_path(self) -> str:
        """Source path used in diagnostics, not an indication of root identity."""
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
        """Normalize and merge sources, with primary values taking precedence.

        Expand environment-style ``__`` paths and convert indexed mappings to
        lists. Nested mappings merge recursively; primary lists replace default
        lists. Neither input's containers are modified.

        :param primary: Values that override defaults.
        :param defaults: Optional fallback values.
        :param _base_path: Diagnostic source path for the result.
        """
        resolved = _resolve(primary or {}, defaults or {}, path_transformer=_norm_path_transform)
        return Configuration(
            resolved, _base_path=_base_path
        )

    @classmethod
    def from_config(cls, base: Mapping | None, *, _base_path: str | None = None) -> Configuration:
        """Fork configuration, preserving its source path and root identity.

        Values in base take precedence; kwargs supply missing defaults rather
        than overwriting existing entries. If base is None, create a scoped
        Configuration from kwargs.
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
        res, found_path = _get_with_path(self, path, default=default, skip_none=skip_none)
        if _is_missing(res):
            if _is_missing(default):
                raise KeyError(path)
            return default, None
        return res, found_path

    def _get(
        self, path: _PathProxy, default: Any = _MISSING, skip_none: bool = False
    ) -> Any:
        """Return the first matched value, raising if absent and no default is given."""
        val, _ = self._get_with_path(path, default=default, skip_none=skip_none)
        return val

    def get(
        self, key: _PathProxy, default: Any = None, skip_none: bool = False
    ) -> Any:
        """Retrieve a value from the configuration by key, returning the default if not found."""
        path = _Path.create(key)
        try:
            return self._get(path, default=default, skip_none=skip_none)
        except KeyError:
            return default

    def has(self, path: _PathProxy) -> bool:
        """Check if the configuration contains the specified keys.

        :param keys: The keys to check.
        :return: True if the keys exist in the configuration, False otherwise.
        """
        path = _Path.create(path)
        try:
            self._get(path)
            return True
        except KeyError:
            return False

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

        :param section: Alternative section paths, tried in order.
        :param default: The default value to return if the section is not found.
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

        :param section: The names of the nested sections to retrieve.
        :return: A list of Configuration objects representing the subsections.
        :raises TypeError: If the section is not a mapping.
        """
        path = _Path.create(section)
        map = _collect_with_paths(self, path)

        if not map:
            return []

        for base_path, v in map.items():
            if not isinstance(v, Mapping):
                raise TypeError(
                    f"Section {self._resolve_path(path)} is not a mapping"
                )

        return [
            Configuration.from_config(v, _base_path=self._resolve_path(base_path))
            for base_path, v in map.items()
        ]

    @overload
    def get_bool(
        self, path: _PathProxy, default: bool | _MissingType = _MISSING
    ) -> bool: ...
    @overload
    def get_bool(
        self, path: _PathProxy, default: None = None
    ) -> bool | None: ...
    def get_bool(
        self, path: _PathProxy, default: bool | None | _MissingType = _MISSING
    ) -> bool | None:
        """Retrieve a boolean value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_bool(val, default, found_path.last if found_path else path.last)

    def get_booln(
        self, path: _PathProxy, default: bool | None = None
    ) -> bool | None:
        """Retrieve a boolean value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved boolean value or the default value if not found.
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
        """Retrieve an integer value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_int(val, default, found_path.last if found_path else path.last)

    def get_intn(
        self, path: _PathProxy, default: int | None = None
    ) -> int | None:
        """Retrieve an integer value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved integer value or the default value if not found.
        """
        return self.get_int(path, default=default)

    @overload
    def get_float(
        self, path: _PathProxy, default: None = None
    ) -> float | None: ...
    @overload
    def get_float(
        self, path: _PathProxy, default: float | _MissingType = _MISSING
    ) -> float: ...
    def get_float(
        self, path: _PathProxy, default: float | None | _MissingType = _MISSING
    ) -> float | None:
        """Retrieve a float value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_float(val, default, found_path.last if found_path else path.last)

    def get_floatn(
        self, path: _PathProxy, default: float | None = None
    ) -> float | None:
        """Retrieve a float value from the configuration, allowing None as default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved float value or the default value if not found.
        """
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
        """Retrieve a string value from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved string value or the default value if not found.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        return _handle_str(val, default, found_path.last if found_path else path.last)

    def get_strn(self, path: _PathProxy, default: str | None = None):
        """Retrieve a string, allowing None as the default.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved string or the default value if not found.
        """
        return self.get_str(path, default=default)

    def get_str_list(
        self, path: _PathProxy, default: list[str] | None = None
    ) -> list[str]:
        """Retrieve a list of strings from the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved list of strings or the default value if not found.
        """
        path = _Path.create(path)
        val, found_path = self._get_with_path(path, default=default, skip_none=True)
        if val is None:
            if default is None:
                return []
            return default
        if isinstance(val, list):
            return _handle_str_list(val, default, found_path.last if found_path else path.last)
        elif isinstance(val, Mapping):
            raise ValueError(
                f"Invalid list value for {str(found_path if found_path else path)}"
            )
        elif not isinstance(val, Mapping):
            before_split = _handle_str(val, None, found_path.last if found_path else path.last)
            if before_split is None:
                return default if default is not None else []
            if "," in before_split:
                return [s.strip() for s in before_split.split(",")]
            return [s.strip() for s in before_split.strip().split()]

    def get_items(
        self, path: _PathProxy, default: dict | None = None
    ) -> Iterable[tuple[Any, Any]]:
        """Retrieve items from a dictionary in the configuration.

        :param keys: The keys of the value to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The retrieved items as a list of key-value tuples or the default value if not found.
        """
        base = _get(self, path, default=default)
        if isinstance(base, Mapping):
            return base.items()
        elif isinstance(base, list):
            return enumerate(base)
        return []

    def collect(self, path: _PathProxy) -> list[Any]:
        return _collect(self, _Path.create(path))

    def collect_str(self, _path: _PathProxy) -> list[str]:
        path = _Path.create(_path)
        vals = _collect(self, path)
        vals = [_handle_str(v, None, path.last) for v in vals if v is not None]
        return [v for v in vals if v is not None]

    def get_scopes(self, _path: _PathProxy) -> list[str]:
        """Retrieve a list of scopes from the configuration.

        :param path: The path of the scopes value to retrieve.
        :return: The scopes as a list, or an empty list if absent.
        """
        path = _Path.create(_path)
        val = self._get(path, default=None, skip_none=True)
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return Configuration.format_scopes(val)
        raise ValueError(f"Invalid scopes value for {path.last}")

    @staticmethod
    def format_scopes(scopes: str | list[str] | None) -> list[str]:
        """Format scopes into a list of strings. If scopes is a string, it will be split by whitespace. If scopes is None, an empty list is returned."""
        if scopes is None:
            return []
        if isinstance(scopes, str):
            scopes = scopes.replace(",", " ")
            lst = scopes.strip().split()
            return [s for s in lst if s]
        return list(scopes)

    @staticmethod
    def _from_config_or_kwargs(primary_config: Mapping | None, kwargs: MutableMapping, *, ensure_root_config: bool = False) -> Configuration:
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
        """Bind a Configuration, reuse a settings instance, or bind defaults.

        None binds an empty scoped Configuration. Plain mappings must instead
        be passed to ``from_mapping``.

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

    Subclasses implement root and scoped binding separately. Dispatch uses only
    ``Configuration.is_root_config``: a root binder locates its own section,
    while a scoped binder reads fields directly. Passing None uses the scoped
    binder with empty configuration.
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
