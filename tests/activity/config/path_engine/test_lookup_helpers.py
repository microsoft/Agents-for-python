# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from types import MappingProxyType

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.activity.config._engine._path._query import _QueryDict
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
def test_get_treats_string_separators_as_literal_and_does_not_ignore_case(factory):
    obj = factory({"Section::Value": 1, "Section": {"Value": 2}})

    assert _get(obj, "Section::Value") == 1
    assert _get(obj, _Path("Section", "Value")) == 2
    assert _get(obj, "section::value", default=_MISSING) is _MISSING
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
    assert _collect_with_paths(obj, path) == {"X": 1, "Y": None}
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
    assert section.has("Value")
    assert not section.has("value")
