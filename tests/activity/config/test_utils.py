# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy
from types import MappingProxyType

import pytest

from microsoft_agents.activity.config._utils import (
    _MISSING,
    _get,
    _is_missing,
    _parse_env_var_name,
    _path,
    _resolve,
    _set,
    _traverse,
    _traverse_leaves,
    _try_set,
    _collect,
    _xpath,
)


@pytest.mark.parametrize("value", [None, False, 0, "", {}, []])
def test_is_missing_distinguishes_unset_from_present_values(value):
    assert _is_missing(_MISSING)
    assert not _is_missing(value)


def test_path_joins_segments():
    assert (
        _path("Connections", "Service", "Settings") == "Connections::Service::Settings"
    )
    assert _path("Connections") == "Connections"
    assert _path() == ""


def test_parse_env_var_name_preserves_single_underscores_and_case():
    assert (
        _parse_env_var_name("Connections__SERVICE_CONNECTION__CLIENT_ID")
        == "Connections::SERVICE_CONNECTION::CLIENT_ID"
    )


@pytest.mark.parametrize("value", [None, False, 0, "", [], {"C": "value"}])
def test_get_returns_raw_values(value):
    mapping = MappingProxyType({"A": MappingProxyType({"B": value})})

    assert _get(mapping, "A::B", default=_MISSING) is value


@pytest.mark.parametrize("path", ["Missing", "A::Missing", "A::B::C"])
def test_get_returns_default_for_missing_or_non_mapping_path(path):
    assert _get({"A": {"B": "scalar"}}, path, default=_MISSING) is _MISSING
    assert _get({"A": {"B": "scalar"}}, path) is None


def test_try_set_creates_nested_mappings():
    mapping = {}

    assert _try_set(mapping, "A::B::C", "value") is True
    assert mapping == {"A": {"B": {"C": "value"}}}


@pytest.mark.parametrize("existing", [None, False, 0, "", {}, []])
def test_try_set_does_not_overwrite_existing_values_by_default(existing):
    mapping = {"A": {"B": existing}}

    assert _try_set(mapping, "A::B", "replacement") is False
    assert mapping["A"]["B"] is existing


def test_try_set_can_explicitly_overwrite():
    mapping = {"A": {"B": "old"}}

    assert _try_set(mapping, "A::B", "new", overwrite=True) is True
    assert mapping == {"A": {"B": "new"}}


@pytest.mark.parametrize("path", ["A::B", "A::B::C"])
def test_try_set_rejects_traversal_through_scalar(path):
    mapping = {"A": "scalar"}

    with pytest.raises(TypeError, match=path):
        _try_set(mapping, path, "value")

    assert mapping == {"A": "scalar"}


def test_try_set_rejects_read_only_mapping():
    mapping = {"A": MappingProxyType({"B": "old"})}

    with pytest.raises(TypeError, match="A::B"):
        _try_set(mapping, "A::B", "new")

    assert mapping["A"]["B"] == "old"


def test_set_overwrites_existing_leaf_and_preserves_siblings():
    mapping = {"A": {"B": "old", "C": "keep"}}

    _set(mapping, "A::B", "new")

    assert mapping == {"A": {"B": "new", "C": "keep"}}


def test_traverse_visits_parents_and_leaves():
    visited = []

    def visit(value, path):
        visited.append((tuple(path), value))

    _traverse({"A": {"B": 1}, "C": 2}, visit)

    assert visited == [(("A",), {"B": 1}), (("A", "B"), 1), (("C",), 2)]


def test_traverse_can_skip_subtree_without_skipping_siblings():
    visited = []

    def visit(value, path):
        visited.append(tuple(path))
        return False if path == ["A"] else None

    _traverse({"A": {"B": 1}, "C": {"D": 2}}, visit)

    assert visited == [("A",), ("C",), ("C", "D")]


def test_traverse_preserves_supplied_path():
    path = ["Root"]
    visited = []

    _traverse({"A": {"B": 1}}, lambda value, parts: visited.append(tuple(parts)), path)

    assert visited == [("Root", "A"), ("Root", "A", "B")]
    assert path == ["Root"]


def test_traverse_leaves_treats_lists_as_values():
    visited = []
    mapping = {"A": {"B": 1}, "C": [{"D": 2}], "E": None}

    _traverse_leaves(mapping, lambda value, path: visited.append((tuple(path), value)))

    assert visited == [(("A", "B"), 1), (("C",), [{"D": 2}]), (("E",), None)]


def test_traverse_leaves_includes_empty_mappings():
    visited = []
    mapping = {"A": {}, "B": {"C": MappingProxyType({})}, "D": 1}

    _traverse_leaves(mapping, lambda value, path: visited.append((tuple(path), value)))

    assert visited == [(("A",), {}), (("B", "C"), {}), (("D",), 1)]


@pytest.mark.parametrize(
    "primary",
    [
        {"App": {"Enabled": "new"}},
        {"App__Enabled": "new"},
        {"App::Enabled": "new"},
    ],
)
def test_resolve_merges_equivalent_path_representations(primary):
    defaults = {"App": {"Enabled": "old", "Name": "keep"}}

    assert _resolve(primary, defaults) == {"App": {"Enabled": "new", "Name": "keep"}}


@pytest.mark.parametrize("value", [None, False, 0, "", "false", "123", []])
def test_resolve_preserves_explicit_primary_values_without_coercion(value):
    assert _resolve({"A__B": value}, {"A": {"B": "default"}}) == {"A": {"B": value}}


def test_resolve_preserves_case_in_both_sources():
    assert _resolve(
        {"app__client_id": "primary"}, {"App": {"CLIENT_ID": "default"}}
    ) == {
        "app": {"client_id": "primary"},
        "App": {"CLIENT_ID": "default"},
    }


def test_resolve_accepts_custom_path_transformer():
    assert _resolve(
        {"App__Name": "new"},
        {"App": {"Name": "old", "Enabled": True}},
        path_transformer=lambda path: path.replace("__", "::"),
    ) == {"App": {"Name": "new", "Enabled": True}}


@pytest.mark.parametrize("primary_first", [True, False])
def test_resolve_rejects_structural_conflicts_between_sources(primary_first):
    scalar = {"A": "scalar"}
    subtree = {"A__B": "child"}
    primary, defaults = (scalar, subtree) if primary_first else (subtree, scalar)

    with pytest.raises((TypeError, ValueError), match="A"):
        _resolve(primary, defaults)


@pytest.mark.parametrize("source", ["primary", "defaults"])
@pytest.mark.parametrize("parent_first", [True, False])
def test_resolve_rejects_conflicting_paths_regardless_of_order(source, parent_first):
    entries = [("A", "scalar"), ("A__B", "child")]
    if not parent_first:
        entries.reverse()
    mapping = dict(entries)
    primary, defaults = (mapping, {}) if source == "primary" else ({}, mapping)

    with pytest.raises((TypeError, ValueError), match="A"):
        _resolve(primary, defaults)


def test_resolve_accepts_read_only_sources_without_modifying_inputs():
    primary = {"A__B": "new"}
    defaults = {"A": {"B": "old", "C": "keep"}}
    original_primary = deepcopy(primary)
    original_defaults = deepcopy(defaults)

    result = _resolve(
        MappingProxyType(primary),
        MappingProxyType({"A": MappingProxyType(defaults["A"])}),
    )

    assert result == {"A": {"B": "new", "C": "keep"}}
    assert primary == original_primary
    assert defaults == original_defaults
    result["A"]["B"] = "changed"
    assert defaults == original_defaults


def test_resolve_empty_sources():
    assert _resolve({}, {}) == {}


@pytest.mark.parametrize("source", ["primary", "defaults"])
def test_resolve_preserves_empty_sections_without_sharing_them(source):
    mapping = {"A": {}, "B": {"C": {}}}
    primary, defaults = (mapping, {}) if source == "primary" else ({}, mapping)

    result = _resolve(primary, defaults)

    assert result == {"A": {}, "B": {"C": {}}}
    assert result["A"] is not mapping["A"]
    assert result["B"]["C"] is not mapping["B"]["C"]
    result["A"]["New"] = 1
    result["B"]["C"]["New"] = 2
    assert mapping == {"A": {}, "B": {"C": {}}}


@pytest.mark.parametrize("empty_is_primary", [True, False])
@pytest.mark.parametrize(
    "empty, populated",
    [
        ({"A": {}}, {"A": {"B": 1}}),
        ({"A": {}}, {"A": {"B": {}}}),
        ({"A": {"B": {}}}, {"A": {"B": {"C": 1}, "D": 2}}),
    ],
)
def test_resolve_merges_empty_and_populated_sections_without_mutating_sources(
    empty_is_primary, empty, populated
):
    primary, defaults = (empty, populated) if empty_is_primary else (populated, empty)
    original_primary = deepcopy(primary)
    original_defaults = deepcopy(defaults)

    result = _resolve(primary, defaults)

    assert result == populated
    assert primary == original_primary
    assert defaults == original_defaults
    result["A"]["New"] = 3
    assert primary == original_primary
    assert defaults == original_defaults


def test_resolve_merges_read_only_empty_section():
    defaults = MappingProxyType({"A": MappingProxyType({})})

    assert _resolve({"A__B": 1}, defaults) == {"A": {"B": 1}}
    assert defaults["A"] == {}


@pytest.mark.parametrize("source", ["primary", "defaults"])
@pytest.mark.parametrize("parent_first", [True, False])
def test_resolve_accepts_empty_parent_and_child_paths_in_either_order(
    source, parent_first
):
    entries = [("A", {}), ("A__B", 1)]
    if not parent_first:
        entries.reverse()
    mapping = dict(entries)
    primary, defaults = (mapping, {}) if source == "primary" else ({}, mapping)

    assert _resolve(primary, defaults) == {"A": {"B": 1}}
    assert mapping["A"] == {}


@pytest.mark.parametrize("empty_is_primary", [True, False])
@pytest.mark.parametrize("scalar", [None, False, 0, "", "scalar", []])
def test_resolve_rejects_non_mapping_parent_of_empty_section(empty_is_primary, scalar):
    empty = {"A": {"B": {}}}
    non_mapping = {"A": scalar}
    primary, defaults = (
        (empty, non_mapping) if empty_is_primary else (non_mapping, empty)
    )

    with pytest.raises((TypeError, ValueError), match="A"):
        _resolve(primary, defaults)


def test_resolve_merges_identical_empty_sections():
    primary = {"A": {}}
    defaults = {"A": {}}

    result = _resolve(primary, defaults)

    assert result == {"A": {}}
    assert result["A"] is not primary["A"]
    assert result["A"] is not defaults["A"]


def test_get_tries_alternative_paths_in_order():
    assert _get({"A": 1, "B": 2}, "Missing", "B", "A") == 2


def test_get_can_skip_null_candidates():
    assert _get({"A": None, "B": False}, "A", "B", skip_none=True) is False


@pytest.mark.parametrize(
    "mapping, path, expected",
    [
        ({"First": 1, "Second": 2}, "Second", [2]),
        ({"Entries": ["first", "second"]}, "Entries::1", ["second"]),
        ({"Entries": {"A": 1, "B": 2}}, "Entries::*", [1, 2]),
        ({"Entries": [1, 2]}, "Entries::*", [1, 2]),
        ({"Entries": [1, 2]}, "Missing::*", []),
    ],
)
def test_collect_selects_named_and_wildcard_paths(mapping, path, expected):
    assert _collect(mapping, path) == expected


def test_xpath_has_stable_alias_precedence():
    assert _xpath("client_id") == ["CLIENTID", "CLIENT_ID", "client_id"]


def test_xpath_joins_path_components():
    assert _xpath("agent_application", "user_authorization") == [
        "AGENTAPPLICATION::USERAUTHORIZATION",
        "AGENT_APPLICATION::USER_AUTHORIZATION",
        "agent_application::user_authorization",
    ]
