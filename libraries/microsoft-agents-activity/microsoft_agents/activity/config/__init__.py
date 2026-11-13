# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Dictionary-backed configuration and typed settings binding.

``Configuration`` wraps nested mappings and sequences, preserving values and
key names. Use string keys for direct lookup and lists of segments for nested
lookup. Internal path objects supply case, underscore, and wildcard policies.

Source resolution, lookup, and settings binding are separate responsibilities.
The internal resolver normalizes and merges sources. The environment
loader accepts a single caller-supplied mapping, delegates normalization to the
resolver, applies logging, and marks its result as application-root input.
Typed getters perform conversion only when values are requested.

Settings classes bind mappings through ``from_config`` and reuse already-bound
instances. Root-aware binders use mapping metadata to distinguish
application-root input from scoped settings. Ordinary mappings and extracted
sections are scoped inputs unless they carry root metadata.

The private ``_engine`` package supplies traversal, mutation, normalization,
and coercion. Underscore-prefixed exports, including path factories, are private
SDK implementation helpers.
"""

from ._load_configuration import load_configuration_from_env
from .configuration import Configuration, _Configurable, _RootConfigurable
from ._protocol import _MappingConfigurable
from ._engine import (
    _MissingType,
    _MISSING,
    _get,
    _is_missing,
    _set,
    _try_set,
    _pop,
    _resolve,
    coerce_bool,
    coerce_int,
    coerce_float,
    _get_str,
    _get_bool,
    _Path,
    _PathProxy,
)
from ._utils import _legpath, _netpath

__all__ = [
    "load_configuration_from_env",
    "Configuration",
    "_MappingConfigurable",
    "_MissingType",
    "_MISSING",
    "_is_missing",
    "_get",
    "_set",
    "_try_set",
    "_pop",
    "_resolve",
    "_Configurable",
    "_RootConfigurable",
    "coerce_bool",
    "coerce_int",
    "coerce_float",
    "_get_str",
    "_get_bool",
    "_Path",
    "_PathProxy",
    "_legpath",
    "_netpath",
]
