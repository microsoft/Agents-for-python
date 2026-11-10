# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Configuration loading and typed settings binding.

``load_configuration_from_env`` returns a root ``Configuration``. Plain mappings
and extracted sections are scoped inputs; ``_RootConfigurable`` distinguishes
these forms using ``Configuration.is_root_config``, not their contents or paths.
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
    _resolve,
    coerce_bool,
    coerce_int,
    coerce_float,
    _get_str,
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
    "_resolve",
    "_Configurable",
    "_RootConfigurable",
    "coerce_bool",
    "coerce_int",
    "coerce_float",
    "_get_str",
    "_Path",
    "_PathProxy",
    "_legpath",
    "_netpath"
]
