# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import MappingProxyType

import pytest

from microsoft_agents.activity.config._engine._path._query import _QueryDict, _QueryList
from microsoft_agents.activity.config._engine._path._utils import (
    _get,
    _pop,
    _set,
    _try_set,
)
from microsoft_agents.activity.config._engine._path.types import (
    _MISSING,
    _Path,
    _UserDict,
    _Wildcard,
)


@pytest.mark.parametrize("factory", [dict, _UserDict, _QueryDict])
def test_try_set_inserts_missing_parents_and_terminal_key(factory):
    obj = factory({})
    path = _Path("Section", "Items", "Value")

    assert _try_set(obj, path, {"Nested": [7]})
    assert _get(obj, path)["Nested"][0] == 7
    assert None not in obj
    if isinstance(obj, _QueryDict):
        assert isinstance(obj["Section"]["Items"]["Value"], _QueryDict)
        assert isinstance(obj["Section"]["Items"]["Value"]["Nested"], _QueryList)


@pytest.mark.parametrize("value", [None, False, 0, "", [], {}])
def test_try_set_preserves_existing_falsy_values_unless_overwrite_is_requested(value):
    obj = {"Section": {"Value": value}}
    path = _Path("Section", "Value")

    assert not _try_set(obj, path, 7)
    assert obj["Section"]["Value"] is value
    assert _try_set(obj, path, 7, overwrite=True)
    assert obj["Section"]["Value"] == 7


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_set_updates_matched_spelling_in_place_and_preserves_siblings(factory):
    obj = factory({"Section": {"Value": 1, "Other": 2}})

    _set(obj, _Path.from_strings("section", "value"), 3)

    assert list(obj["Section"]) == ["Value", "Other"]
    assert obj["Section"]["Value"] == 3
    assert obj["Section"]["Other"] == 2


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_set_traverses_existing_lists_and_assigns_terminal_list_elements(factory):
    obj = factory({"Items": [{"Value": 1}, 2]})

    _set(obj, _Path("Items", "0", "Value"), 3)
    _set(obj, _Path("Items", "1"), {"Nested": 4})

    assert obj["Items"][0]["Value"] == 3
    assert obj["Items"][1]["Nested"] == 4
    assert not _try_set(obj, _Path("Items", "1"), "replacement")
    if isinstance(obj, _QueryDict):
        assert isinstance(obj["Items"][1], _QueryDict)


@pytest.mark.parametrize("factory", [list, _QueryList])
def test_set_accepts_list_roots(factory):
    obj = factory([{"Value": 1}, 2])

    _set(obj, _Path("0", "Value"), 3)
    _set(obj, _Path("1"), 4)

    assert obj[0]["Value"] == 3
    assert obj[1] == 4


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize("operation", [_set, _pop])
def test_mutation_helpers_accept_integer_paths_for_list_roots(index, operation):
    obj = [7, 8]
    if operation is _set:
        operation(obj, index, 9)
        assert obj[index] == 9
    else:
        assert operation(obj, index) == [7, 8][index]
        assert obj == ([8] if index == 0 else [7])


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_set_rejects_absent_terminal_index_without_changing_list(factory):
    obj = factory({"Items": [7]})

    with pytest.raises(IndexError):
        _set(obj, _Path("Items", "5"), 9)

    assert list(obj["Items"]) == [7]


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_set_rejects_absent_intermediate_index_without_appending(factory):
    obj = factory({"Items": []})

    with pytest.raises(RuntimeError, match="intermediary"):
        _set(obj, _Path("Items", "5", "Value"), 9)

    assert list(obj["Items"]) == []


@pytest.mark.parametrize(
    "obj",
    [
        {"Section": 7},
        {"Section": MappingProxyType({"Value": 1})},
        MappingProxyType({}),
    ],
)
def test_set_rejects_scalar_or_read_only_targets(obj):
    with pytest.raises(TypeError):
        _set(obj, _Path("Section", "Value"), 9)


@pytest.mark.parametrize("factory", [dict, _QueryDict])
@pytest.mark.parametrize("value", [None, False, 0, 7])
def test_pop_returns_present_values_and_only_deletes_the_matched_key(factory, value):
    obj = factory({"Section": {"Value": value, "Other": 2}})

    assert _pop(obj, _Path("Section", "Value"), default=_MISSING) is value
    assert _get(obj, _Path("Section", "Value"), default=_MISSING) is _MISSING
    assert obj["Section"]["Other"] == 2
    assert _pop(obj, _Path("Section", "Value"), default=_MISSING) is _MISSING


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_pop_deletes_list_leaf_using_an_integer_index(factory):
    obj = factory({"Items": [None, 7]})

    assert _pop(obj, _Path("Items", "0"), default=_MISSING) is None
    assert list(obj["Items"]) == [7]
    assert _pop(obj, _Path("Items", "5"), default=_MISSING) is _MISSING


def test_pop_rejects_a_read_only_parent_without_modifying_it():
    parent = MappingProxyType({"Value": 7})

    with pytest.raises(TypeError, match="non-mutable"):
        _pop({"Section": parent}, _Path("Section", "Value"))

    assert parent["Value"] == 7


@pytest.mark.parametrize("operation", [_set, _pop])
@pytest.mark.parametrize(
    "path", [_Path(), _Path(_Wildcard()), _Path("Section", _Wildcard())]
)
def test_mutation_helpers_reject_empty_or_wildcard_paths_before_mutation(
    operation, path
):
    obj = {"Section": {"Value": 7}}

    with pytest.raises(ValueError):
        if operation is _set:
            operation(obj, path, 9)
        else:
            operation(obj, path)

    assert obj == {"Section": {"Value": 7}}
