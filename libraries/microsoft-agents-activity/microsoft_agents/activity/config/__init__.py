# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Read application settings and create SDK settings objects.

Use ``Configuration`` for nested dictionaries and lists, with methods such as
``get_int`` and ``get_bool`` to convert values when reading them. Use
``load_configuration_from_env`` for environment-style names such as
``CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENT_ID``.

For nested lookup, pass a list of keys, such as ``["service", "timeout"]``.
Use integer indexes for lists and ``wildcard()`` to collect values from all keys
at a dictionary level. The string ``"*"`` is a literal key.

SDK settings classes provide ``from_config`` to read a dictionary or
Configuration instead of supplying each constructor argument separately.
See each class's examples for the dictionary shape it expects.

Names starting with an underscore, including the path factories and ``_engine``
package, are internal implementation helpers.
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
from ._utils import _legpath, _netpath, wildcard

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
    "wildcard",
]
