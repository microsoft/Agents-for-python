# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import UserDict
from copy import copy
from types import MappingProxyType

import pytest

from microsoft_agents.activity.config._engine._path._query import (
    _normalize_value,
    _QueryDict,
    _QueryList,
)
from microsoft_agents.activity.config._engine._path.types import _Path, _UserList


def test_normalization_recursively_wraps_read_only_mappings_and_sequences():
    source = MappingProxyType({"Items": ({"Value": 7},), "Text": "hello"})

    result = _normalize_value(source)

    assert isinstance(result, _QueryDict)
    assert isinstance(result["Items"], _QueryList)
    assert isinstance(result["Items"][0], _QueryDict)
    assert result[_Path("Items", "0", "Value")] == 7
    assert result["Text"] == "hello"
    assert isinstance(source["Items"], tuple)


@pytest.mark.parametrize("factory", [_QueryDict, _QueryList])
def test_normalization_reuses_already_normalized_containers(factory):
    wrapped = factory({})

    assert _normalize_value(wrapped) is wrapped


def test_query_dict_exact_and_explicit_matching_reads():
    wrapped = _QueryDict({"Client_Id": 1, "CLIENT_ID": 2, "ClientId": 3})

    assert wrapped["Client_Id"] == 1
    assert wrapped["CLIENT_ID"] == 2
    with pytest.raises(KeyError):
        wrapped["client_id"]
    assert wrapped[_Path.from_strings("client_id")] == 1
    assert wrapped[_Path.from_strings("clientid", ignore_underscores=True)] == 1


def test_query_dict_path_read_backtracks_and_walks_lists():
    wrapped = _QueryDict({"Section": {}, "section": {"Items": [{"Value": None}]}})
    path = _Path.from_strings("section", "items", "0", "value")

    assert wrapped[path] is None
    with pytest.raises(KeyError):
        wrapped[_Path("missing", "value")]


def test_query_dict_path_membership_through_lists_matches_subscription():
    wrapped = _QueryDict({"Items": [{"Value": None}]})
    path = _Path("Items", "0", "Value")

    assert wrapped[path] is None
    assert path in wrapped


@pytest.mark.parametrize("operation", ["set", "update", "setdefault", "ior"])
def test_query_dict_mutators_normalize_values_and_update_the_index(operation):
    wrapped = _QueryDict()
    value = {"Nested": [{"Value": 7}]}
    if operation == "set":
        wrapped["Section"] = value
    elif operation == "update":
        wrapped.update({"Section": value})
    elif operation == "setdefault":
        wrapped.setdefault("Section", value)
    else:
        wrapped |= UserDict({"Section": value})

    assert isinstance(wrapped["Section"], _QueryDict)
    assert isinstance(wrapped["Section"]["Nested"], _QueryList)
    assert wrapped[_Path.from_strings("section", "nested", "0", "value")] == 7


def test_query_dict_matched_update_preserves_spelling_and_insertion_order():
    wrapped = _QueryDict({"Section": {"Value": 1, "Other": 2}})

    wrapped[_Path.from_strings("section", "value")] = 3

    assert list(wrapped["Section"]) == ["Value", "Other"]
    assert wrapped[_Path("Section", "Value")] == 3


@pytest.mark.parametrize("factory", [copy, lambda value: value.copy()])
def test_query_dict_copy_has_an_independent_index(factory):
    original = _QueryDict({"Value": 1})
    cloned = factory(original)

    cloned["Value"] = 2
    del cloned["Value"]
    cloned["Other"] = 3

    assert original["Value"] == 1
    assert original[_Path.from_strings("value")] == 1
    assert "Other" not in original
    assert cloned[_Path.from_strings("other")] == 3
    with pytest.raises(KeyError):
        cloned["Value"]


@pytest.mark.parametrize("operation", ["del", "pop", "clear"])
def test_query_dict_removal_keeps_index_consistent(operation):
    wrapped = _QueryDict({"Value": None})
    if operation == "del":
        del wrapped["Value"]
    elif operation == "pop":
        assert wrapped.pop("Value") is None
    else:
        wrapped.clear()

    assert not wrapped
    assert "Value" not in wrapped
    with pytest.raises(KeyError):
        wrapped[_Path.from_strings("value")]


def test_query_dict_missing_deletion_raises_without_touching_siblings():
    wrapped = _QueryDict({"Section": {"Keep": 1}})

    with pytest.raises(KeyError):
        del wrapped[_Path("Section", "Missing")]

    assert wrapped[_Path("Section", "Keep")] == 1


@pytest.mark.parametrize("operation", ["set", "append", "insert", "extend", "iadd"])
def test_query_list_mutators_recursively_normalize_values(operation):
    wrapped = _QueryList([0] if operation == "set" else [])
    value = {"Nested": [{"Value": 7}]}
    if operation == "set":
        wrapped[0] = value
    elif operation == "append":
        wrapped.append(value)
    elif operation == "insert":
        wrapped.insert(0, value)
    elif operation == "extend":
        wrapped.extend(item for item in [value])
    else:
        original = wrapped
        wrapped += _UserList([value])
        assert wrapped is original

    assert isinstance(wrapped[0], _QueryDict)
    assert isinstance(wrapped[0]["Nested"], _QueryList)
    assert wrapped[_Path("0", "Nested", "0", "Value")] == 7


@pytest.mark.parametrize("operation", ["extend", "iadd"])
def test_query_list_self_extension_uses_a_finite_snapshot(operation):
    wrapped = _QueryList([{"Value": 7}])
    original = wrapped
    if operation == "extend":
        wrapped.extend(wrapped)
    else:
        wrapped += wrapped

    assert wrapped is original
    assert len(wrapped) == 2
    assert wrapped[0] is wrapped[1]


def test_query_list_extension_propagates_iterator_errors_and_keeps_partial_progress():
    def values():
        yield {"Value": 7}
        raise RuntimeError("source failed")

    wrapped = _QueryList([])
    with pytest.raises(RuntimeError, match="source failed"):
        wrapped.extend(values())

    assert len(wrapped) == 1
    assert isinstance(wrapped[0], _QueryDict)


def test_query_list_membership_checks_values_not_indexes():
    wrapped = _QueryList(["read", None])

    assert "read" in wrapped
    assert None in wrapped
    assert 0 not in wrapped
    assert "missing" not in wrapped


@pytest.mark.parametrize(
    "factory",
    [
        copy,
        lambda value: value.copy(),
        lambda value: value[:],
        lambda value: value + [{"Value": 8}],
        lambda value: [{"Value": 8}] + value,
        lambda value: value * 2,
    ],
)
def test_query_list_factories_preserve_normalization_and_independent_storage(factory):
    original = _QueryList([{"Value": 7}])

    result = factory(original)
    result.append({"Value": 9})

    assert isinstance(result, _QueryList)
    assert all(isinstance(item, _QueryDict) for item in result)
    assert len(original) == 1


def test_query_list_slice_assignment_normalizes_replacements():
    wrapped = _QueryList([{"Value": 1}, {"Value": 2}])

    wrapped[:1] = [{"Value": 3}, {"Value": 4}]

    assert [item["Value"] for item in wrapped] == [3, 4, 2]
    assert all(isinstance(item, _QueryDict) for item in wrapped)


def test_query_list_slice_assignment_normalizes_nested_generator_values():
    wrapped = _QueryList([0])

    wrapped[:] = ({"Items": [{"Value": value}]} for value in (1, 2))

    assert [item["Items"][0]["Value"] for item in wrapped] == [1, 2]
    assert all(isinstance(item, _QueryDict) for item in wrapped)
    assert all(isinstance(item["Items"], _QueryList) for item in wrapped)
    assert all(isinstance(item["Items"][0], _QueryDict) for item in wrapped)


def test_query_list_slice_self_assignment_materializes_values_before_mutating():
    wrapped = _QueryList([{"Value": 1}, {"Value": 2}])
    original_items = list(wrapped)

    wrapped[1:1] = wrapped

    assert [item["Value"] for item in wrapped] == [1, 1, 2, 2]
    assert wrapped[1] is original_items[0]
    assert wrapped[2] is original_items[1]


def test_query_list_extended_slice_assignment_normalizes_replacements():
    wrapped = _QueryList([0, 1, 2, 3])

    wrapped[::2] = [{"Value": 7}, {"Value": 8}]

    assert wrapped[0]["Value"] == 7
    assert wrapped[2]["Value"] == 8
    assert wrapped[1] == 1
    assert wrapped[3] == 3
    assert isinstance(wrapped[0], _QueryDict)
    assert isinstance(wrapped[2], _QueryDict)


def test_query_list_extended_slice_length_mismatch_leaves_original_unchanged():
    wrapped = _QueryList([0, 1, 2])

    with pytest.raises(ValueError, match="extended slice"):
        wrapped[::2] = [{"Value": 7}]

    assert wrapped == [0, 1, 2]


def test_query_list_slice_assignment_propagates_iterator_failure_without_mutating():
    def values():
        yield {"Value": 7}
        raise RuntimeError("source failed")

    wrapped = _QueryList([0, 1])
    with pytest.raises(RuntimeError, match="source failed"):
        wrapped[:] = values()

    assert wrapped == [0, 1]


@pytest.mark.parametrize(
    "index, expected",
    [
        (slice(1, 3), [0, 3]),
        (slice(None, None, 2), [1, 3]),
        (slice(None, None, -1), []),
    ],
)
def test_query_list_slice_deletion_preserves_remaining_normalized_items(
    index, expected
):
    wrapped = _QueryList([{"Value": value} for value in range(4)])

    del wrapped[index]

    assert [item["Value"] for item in wrapped] == expected
    assert all(isinstance(item, _QueryDict) for item in wrapped)
