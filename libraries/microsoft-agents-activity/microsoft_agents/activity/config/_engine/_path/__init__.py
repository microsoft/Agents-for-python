# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Internal path types, query containers, traversal, and mutation helpers.

A path is a sequence of segment policies. Simple segments can optionally ignore
case and/or underscores. Wildcard segments enumerate mappings, while sequence
traversal requires integer-valued segments and supports negative indexes.
Numeric strings do not index sequences. Single-value lookup and mutation reject
wildcards.

Query dictionaries maintain casefolded, underscore-free candidate buckets.
Every candidate is checked against the requested segment policy, preserving
source spelling and insertion order. More than one spelling can match a simple
segment, so lookup and deletion backtrack when an earlier candidate has no
matching descendant. Assignment selects parents greedily; see ``_try_set`` for
ambiguous-path limitations.

Traversal retains the original path, advances an integer cursor, and maintains
a stack of actual source keys. Value-only lookup does not materialize paths;
matched-path lookup copies keys only when a result is found. Collection results
are keyed by rendered full matched paths. Repeated leaf names under different
paths remain separate; duplicate rendered paths raise ``KeyError``.

Mapping mutation can create missing mapping parents but does not grow lists to
satisfy missing indexes. Query-container mutations normalize new values and keep
indexes synchronized. Copies isolate the outer container and index while
allowing already-wrapped descendants to remain shared. List membership uses
ordinary value equality.
"""

from .types import (
    _PathSegment,
    _Wildcard,
    _SimplePathSegment,
    _UserDict,
    _UserList,
    _Path,
    _PathProxy,
    _MISSING,
    _MissingType,
    _is_missing,
)

from ._utils import (
    _get_with_path,
    _get,
    _collect_with_paths,
    _collect,
    _try_set,
    _set,
    _pop,
)
from ._query import _QueryDict

__all__ = [
    "_PathSegment",
    "_Wildcard",
    "_SimplePathSegment",
    "_UserDict",
    "_UserList",
    "_Path",
    "_PathProxy",
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
    "_QueryDict",
]
