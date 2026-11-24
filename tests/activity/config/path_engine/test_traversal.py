# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import MappingProxyType

import pytest

from microsoft_agents.activity.config._engine._path._query import _QueryDict, _QueryList
from microsoft_agents.activity.config._engine._path._step import iter_steps, step_once
from microsoft_agents.activity.config._engine._path._traverse import (
    _lookup,
    _traverse,
    _traverse_leaves,
    _TraverseState,
)
from microsoft_agents.activity.config._engine._path.types import (
    _Path,
    _SimplePathSegment,
    _UserDict,
    _Wildcard,
)


@pytest.mark.parametrize("factory", [dict, MappingProxyType, _UserDict, _QueryDict])
def test_mapping_steps_preserve_source_keys_and_candidate_order(factory):
    obj = factory({"Client_Id": 1, "CLIENT_ID": 2, "ClientId": 3})

    matches = list(iter_steps(_SimplePathSegment("client_id", ignore_case=True), obj))

    assert matches == [("Client_Id", 1), ("CLIENT_ID", 2)]
    assert step_once(_SimplePathSegment("ClientId"), obj) == (True, "ClientId", 3)
    assert step_once(_SimplePathSegment("missing"), obj) == (False, None, None)


@pytest.mark.parametrize("factory", [list, tuple, _QueryList])
def test_sequence_steps_return_integer_indexes_and_handle_missing_positions(factory):
    obj = factory([None, 7])

    assert list(iter_steps(_SimplePathSegment(0), obj)) == [(0, None)]
    assert step_once(_SimplePathSegment(1), obj) == (True, 1, 7)
    assert step_once(_SimplePathSegment(2), obj) == (False, None, None)
    assert step_once(_SimplePathSegment("value"), obj) == (False, None, None)


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_wildcard_steps_enumerate_all_mapping_entries(factory):
    obj = factory({"A": 1, "B": None})

    assert list(iter_steps(_Wildcard(), obj)) == [("A", 1), ("B", None)]


def test_leaf_traversal_restores_prefix_cursor_and_parent_between_siblings():
    obj = _QueryDict({"Left": {"X": 1}, "Right": {"Y": 2}})
    path = _Path(_Wildcard(), _Wildcard())
    visited = []

    def handler(state, value):
        visited.append(
            (str(state.traversed_path()), state.path_index, state.current, value)
        )

    _traverse_leaves(path, obj, handler)

    assert [(key, index, value) for key, index, _, value in visited] == [
        ("Left::X", 2, 1),
        ("Right::Y", 2, 2),
    ]
    assert visited[0][2] is obj["Left"]
    assert visited[1][2] is obj["Right"]
    assert len(path) == 2


def test_inner_traversal_visits_prefixes_and_can_stop_before_descending():
    obj = {"Section": {"Value": 7}}
    visited = []

    def handler(state, value):
        visited.append(str(state.traversed_path()))
        state.finished = True

    _traverse(_Path("Section", "Value"), obj, handler)

    assert visited == ["Section"]


def test_inner_traversal_visits_both_parent_and_leaf():
    visited = []

    def handler(state, value):
        visited.append((str(state.traversed_path()), value))

    _traverse(_Path("Section", "Value"), {"Section": {"Value": 7}}, handler)

    assert visited == [("Section", {"Value": 7}), ("Section::Value", 7)]


def test_lookup_backtracks_after_a_matching_prefix_without_the_required_leaf():
    obj = _QueryDict({"Section": {}, "section": {"Value": 7}})

    result = _lookup(obj, _Path.from_strings("section", "value"), include_path=True)

    assert result.found
    assert result.value == 7
    assert result.matched_keys == ["section", "Value"]


def test_lookup_returns_snapshot_of_all_source_keys_including_list_indexes():
    obj = _QueryDict({"Section": {"Items": [{"Value": 7}]}})
    path = _Path.from_strings("section", "items", 0, "value")

    first = _lookup(obj, path, include_path=True)
    second = _lookup(obj, path, include_path=True)
    first.matched_keys.append("local")

    assert first.value == second.value == 7
    assert second.matched_keys == ["Section", "Items", 0, "Value"]
    assert _lookup(obj, path).matched_keys is None


def test_traverse_states_do_not_share_matched_key_storage():
    first = _TraverseState(_Path("Value"), {})
    second = _TraverseState(_Path("Value"), {})

    first.traversed_keys.append("Value")

    assert second.traversed_keys == []


@pytest.mark.parametrize("path", ["", [], _Path(), _Wildcard(), _Path(_Wildcard())])
def test_singular_path_validation_rejects_empty_or_wildcard_paths(path):
    with pytest.raises(ValueError):
        _lookup({}, path)


@pytest.mark.parametrize("factory", [dict, MappingProxyType, _UserDict, _QueryDict])
@pytest.mark.parametrize("stored_key", ["01", "\u0661", "\uff11"])
def test_mapping_steps_preserve_literal_decimal_spellings_for_all_mapping_wrappers(
    factory, stored_key
):
    obj = factory({stored_key: 7})

    assert list(iter_steps(_SimplePathSegment("1"), obj)) == []
    assert list(iter_steps(_SimplePathSegment(stored_key), obj)) == [(stored_key, 7)]


@pytest.mark.parametrize("factory", [list, tuple, _QueryList])
@pytest.mark.parametrize("segment", ["0", "1", "-1", "1.0", " 1", "1 "])
def test_sequence_steps_do_not_coerce_string_indexes(factory, segment):
    obj = factory([7, 8])

    assert list(iter_steps(_SimplePathSegment(segment), obj)) == []


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_traversal_backtracks_through_scalar_and_short_list_candidates(factory):
    obj = factory(
        {
            "Section": 7,
            "SECTION": {"Items": []},
            "section": {"Items": [0, {"Value": 9}]},
        }
    )
    path = _Path.from_strings("section", "items", 1, "value")

    result = _lookup(obj, path, include_path=True)

    assert result.found
    assert result.value == 9
    assert result.matched_keys == ["section", "Items", 1, "Value"]


@pytest.mark.parametrize("traverse", [_traverse, _traverse_leaves])
def test_traversal_propagates_handler_failure_without_visiting_later_siblings(traverse):
    visited = []

    def handler(state, value):
        visited.append(str(state.traversed_path()))
        raise RuntimeError("handler failed")

    with pytest.raises(RuntimeError, match="handler failed"):
        traverse(_Path(_Wildcard()), {"First": 1, "Second": 2}, handler)

    assert visited == ["First"]
