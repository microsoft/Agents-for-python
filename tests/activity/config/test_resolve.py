# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy
from types import MappingProxyType

import pytest

from microsoft_agents.activity.config import Configuration
from microsoft_agents.activity.config._resolve import _normalize, _resolve


@pytest.mark.parametrize(
    "indices",
    [
        {"10": "ten", "2": "two", "0": "zero"},
        {10: "ten", 2: "two", 0: "zero"},
    ],
)
def test_normalize_sorts_indexed_mappings_numerically(indices):
    source = {"Values": MappingProxyType(indices), "Empty": {}, "List": []}

    assert _normalize(MappingProxyType(source)) == {
        "Values": ["zero", "two", "ten"],
        "Empty": {},
        "List": [],
    }


def test_normalize_rejects_duplicate_list_indices():
    with pytest.raises(ValueError, match="Duplicate configuration list indices"):
        _normalize({"Values": {"0": "first", "00": "second"}})


@pytest.mark.parametrize(
    "primary",
    [
        {"Scopes": ["admin"]},
        {"Scopes": {"0": "admin"}},
        {"Scopes__0": "admin"},
    ],
)
@pytest.mark.parametrize(
    "defaults",
    [
        {"Scopes": ["read", "write"]},
        {"Scopes__0": "read", "Scopes__1": "write"},
    ],
)
def test_resolve_replaces_whole_lists_regardless_of_representation(primary, defaults):
    original_primary = deepcopy(primary)
    original_defaults = deepcopy(defaults)

    assert _resolve(primary, defaults) == {"Scopes": ["admin"]}
    assert primary == original_primary
    assert defaults == original_defaults


def test_resolve_replaces_list_entries_without_inheriting_nested_defaults():
    defaults = {
        "App": {"Entries": [{"Name": "default", "Scopes": ["read"]}], "Keep": 1}
    }
    primary = {"App": {"Entries": [{"Name": "custom"}]}}

    assert _resolve(primary, defaults) == {
        "App": {"Entries": [{"Name": "custom"}], "Keep": 1}
    }


def test_resolve_empty_primary_list_clears_indexed_defaults():
    assert _resolve({"Scopes": []}, {"Scopes__0": "read", "Scopes__1": "write"}) == {
        "Scopes": []
    }


@pytest.mark.parametrize("as_defaults", [True, False])
@pytest.mark.parametrize(
    "entries",
    [
        [{"Scopes": {"0": "read"}}],
        [{"Groups": [{"Scopes": {"0": "read"}}]}],
        [[{"Scopes": {"0": "read"}}]],
    ],
)
def test_configuration_resolution_copies_all_nested_containers(as_defaults, entries):
    source = {"Entries": entries}
    original = deepcopy(source)
    if as_defaults:
        result = Configuration.from_mapping({"Unrelated": True}, **source)
    else:
        result = Configuration.from_mapping(source, Unrelated=True)

    assert source == original
    assert result["Entries"] is not entries
    if isinstance(entries[0], list):
        scopes = result["Entries"][0][0]["Scopes"]
    elif "Groups" in entries[0]:
        scopes = result["Entries"][0]["Groups"][0]["Scopes"]
    else:
        scopes = result["Entries"][0]["Scopes"]
    assert scopes == ["read"]
    scopes.append("write")
    assert source == original


def test_normalize_copies_read_only_mappings_inside_nested_lists():
    scopes = {"0": "read"}
    source = {
        "Entries": [
            [MappingProxyType({"Scopes": MappingProxyType(scopes)})],
            [],
        ]
    }

    result = _normalize(source)

    assert result == {"Entries": [[{"Scopes": ["read"]}], []]}
    result["Entries"][0][0]["Scopes"].append("write")
    assert scopes == {"0": "read"}
