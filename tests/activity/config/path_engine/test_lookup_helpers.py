# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import MappingProxyType

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.activity.config._engine._path._query import _QueryDict, _QueryList
from microsoft_agents.activity.config._engine._path._utils import (
    _collect,
    _collect_with_paths,
    _get,
    _get_with_path,
)
from microsoft_agents.activity.config._engine._path.types import (
    _MISSING,
    _Path,
    _UserDict,
    _Wildcard,
)
from microsoft_agents.activity.config._utils import _legpath


@pytest.mark.parametrize("factory", [dict, MappingProxyType, _UserDict, _QueryDict])
@pytest.mark.parametrize("value", [None, False, 0, "", [], {"Other": 1}])
def test_get_preserves_raw_leaf_values_and_distinguishes_missing(factory, value):
    obj = factory({"Section": {"Value": value}})

    result = _get(obj, _Path("Section", "Value"), default=_MISSING)

    assert result is obj["Section"]["Value"]
    assert _get(obj, _Path("Section", "Missing"), default=_MISSING) is _MISSING


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_get_rejects_delimited_segments_and_uses_explicit_nested_paths(factory):
    obj = factory({"Section": {"Value": 2}})

    with pytest.raises(ValueError, match="must not contain"):
        _get(obj, "Section::Value")
    assert _get(obj, _Path("Section", "Value")) == 2
    assert _get(obj, _Path("section", "value"), default=_MISSING) is _MISSING
    assert _get(obj, _legpath("section", "value")) == 2


@pytest.mark.parametrize("factory", [dict, _QueryDict])
@pytest.mark.parametrize("path", [_Path("Missing"), _Path("Section", "Value", "Child")])
def test_get_with_path_returns_default_and_no_path_for_unmatched_queries(factory, path):
    obj = factory({"Section": {"Value": 7}})
    default = object()

    assert _get(obj, path, default=default) is default
    assert _get_with_path(obj, path, default=default) == (default, None)


@pytest.mark.parametrize("index", [0, 1])
def test_lookup_helpers_accept_integer_paths_for_list_roots(index):
    obj = [7, 8]

    assert _get(obj, index) == obj[index]
    value, matched = _get_with_path(obj, index)
    assert value == obj[index]
    assert str(matched) == str(index)


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_skip_none_continues_search_but_none_is_missing_does_not(factory):
    obj = factory({"Section": {"Value": None}, "section": {"Value": 7}})
    path = _Path.from_strings("section", "value")

    assert _get(obj, path, default=42) is None
    assert _get(obj, path, default=42, none_is_missing=True) == 42
    assert _get(obj, path, default=42, skip_none=True) == 7
    assert _get_with_path(obj, path, default=42, none_is_missing=True) == (42, None)
    value, matched = _get_with_path(obj, path, skip_none=True)
    assert value == 7
    assert str(matched) == "section::Value"


def test_value_only_get_does_not_materialize_a_result_path(monkeypatch):
    obj = _QueryDict({"Section": {"Value": 7}})
    path = _Path("Section", "Value")

    def unexpected_path(*args, **kwargs):
        pytest.fail("A value-only lookup must not construct its matched path")

    monkeypatch.setattr(_Path, "exact", unexpected_path)

    assert _get(obj, path) == 7
    assert Configuration(obj).get(path) == 7


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_collect_preserves_order_and_can_skip_none(factory):
    obj = factory({"Left": {"X": 1}, "Right": {"Y": None}})
    path = _Path(_Wildcard(), _Wildcard())

    assert _collect(obj, path) == [1, None]
    assert _collect(obj, path, skip_none=True) == [1]
    entries = _collect_with_paths(obj, path)
    assert list(entries) == ["X", "Y"]
    assert [entry.value for entry in entries.values()] == [1, None]
    assert [str(entry.path) for entry in entries.values()] == ["Left::X", "Right::Y"]
    assert _collect(obj, _Path("Missing")) == []


def test_collect_rejects_duplicate_leaf_names_without_silently_overwriting():
    obj = {"Left": {"Value": 1}, "Right": {"Value": 2}}

    with pytest.raises(KeyError, match="Duplicate key"):
        _collect_with_paths(obj, _Path(_Wildcard(), "Value"))


def test_public_configuration_getters_and_section_paths_use_shared_lookup():
    config = Configuration(
        {"Outer": {"Inner": {"Value": "7", "Scopes": ["read", "write"]}}}
    )
    section = config.get_section(_Path("Outer", "Inner"))

    assert section.base_path == "Outer::Inner"
    assert section.get_int("Value") == 7
    assert section.get_scopes("Scopes") == ["read", "write"]
    assert section.get("value") is None
    assert section.get("Missing", 42) == 42


@pytest.mark.parametrize("getter", [_get, _get_with_path])
@pytest.mark.parametrize("path", [[""], ["", ""], _Path()])
def test_getters_consistently_reject_paths_that_normalize_to_empty(getter, path):
    with pytest.raises(ValueError):
        getter({"Value": 7}, path)


@pytest.mark.parametrize("factory", [dict, _QueryDict])
@pytest.mark.parametrize("value", [False, 0, "", [], {}])
def test_skip_none_selects_present_falsy_leaf_before_later_truthy_match(factory, value):
    obj = factory(
        {
            "SECTION": {"Value": None},
            "Section": {"Value": value},
            "section": {"Value": 9},
        }
    )
    path = _Path.from_strings("section", "value")

    found, matched = _get_with_path(
        obj, path, default=_MISSING, skip_none=True, none_is_missing=True
    )

    assert found == value
    assert str(matched) == "Section::Value"
    assert _get(obj, matched, default=_MISSING) is found


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_collection_checks_duplicate_names_only_after_skipping_none(factory):
    obj = factory({"Left": {"Value": None}, "Right": {"Value": 7}})
    path = _Path(_Wildcard(), "Value")

    entries = _collect_with_paths(obj, path, skip_none=True)
    assert list(entries) == ["Value"]
    assert entries["Value"].value == 7
    assert str(entries["Value"].path) == "Right::Value"
    assert _collect(obj, path, skip_none=True) == [7]
    with pytest.raises(KeyError, match="Duplicate key"):
        _collect(obj, path)


@pytest.mark.parametrize("factory", [dict, _QueryDict])
def test_matched_paths_replay_literal_wildcard_keys(factory):
    obj = factory({"Section": {"*": {"Value": None}}})
    path = _Path.from_strings("SECTION", "*", "VALUE")

    value, matched = _get_with_path(obj, path, default=_MISSING)

    assert value is None
    assert [segment.string for segment in matched] == ["Section", "*", "Value"]
    assert matched.is_simple
    assert _get(obj, matched, default=_MISSING) is None


@pytest.mark.parametrize("factory", [list, _QueryList])
@pytest.mark.parametrize("digit", ["\u00b2", "\u2081", "\u2460"])
def test_nondecimal_digit_paths_do_not_match_list_indexes(factory, digit):
    obj = factory([7, 8])

    assert _get(obj, digit, default=_MISSING) is _MISSING
    assert _get_with_path(obj, digit, default=_MISSING) == (_MISSING, None)
