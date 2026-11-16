# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Internal mechanisms shared by configuration wrappers and settings binders.

The path layer operates directly on a nested tree of mappings and sequences.
Query wrappers normalize nested containers and maintain per-mapping folded-key
indexes. Policies on path segments determine which original keys match,
preserving their names.

Raw lookup is independent of typed conversion. ``_MISSING`` distinguishes
absence from a stored ``None``, while coercion helpers apply the caller's default
and validation rules. Value-only lookup avoids constructing a matched path;
callers needing source spelling request it explicitly.

Source resolution is a separate preprocessing operation with its own name
transformation and merge rules. The outer configuration layer manages
root/scoped binding metadata.

This private package supplies shared implementation tools.
"""

from ._coercion import (
    _handle_bool,
    _handle_int,
    _handle_float,
    _handle_str,
    _handle_str_list,
    coerce_bool,
    coerce_int,
    coerce_float,
    _get_str,
    _get_bool,
)
from ._path import (
    _Path,
    _PathProxy,
    _PathSegment,
    _SimplePathSegment,
    _Wildcard,
    _get_with_path,
    _get,
    _collect_with_paths,
    _collect,
    _try_set,
    _set,
    _pop,
    _QueryDict,
)
from ._path.types._missing import _MISSING, _MissingType, _is_missing
from ._resolve import _resolve
from ._utils import _parse_env_var_name

__all__ = [
    "_Path",
    "_PathProxy",
    "_PathSegment",
    "_SimplePathSegment",
    "_Wildcard",
    "_QueryDict",
    "_MISSING",
    "_MissingType",
    "_is_missing",
    "_get_with_path",
    "_get",
    "_collect_with_paths",
    "_collect",
    "_try_set",
    "_set",
    "_pop",
    "_resolve",
    "_parse_env_var_name",
    "_handle_bool",
    "_handle_int",
    "_handle_float",
    "_handle_str",
    "_handle_str_list",
    "coerce_bool",
    "coerce_int",
    "coerce_float",
    "_get_str",
    "_get_bool",
]
