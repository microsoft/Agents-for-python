# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config._engine._path._folded_map import (
    _FoldedMap,
    _get_folded_key,
    _ps,
)
from microsoft_agents.activity.config._engine._path.types import (
    _SimplePathSegment,
)


def test_segment_conversion_preserves_explicit_matching_policy():
    segment = _SimplePathSegment("Client_Id", ignore_case=True)

    assert _ps(segment) is segment
    assert _ps("Client_Id").check("Client_Id")
    assert not _ps("Client_Id").check("client_id")
    assert _get_folded_key(segment) == _get_folded_key("CLIENTID")


def test_colliding_folded_names_remain_distinct_and_query_policy_selects_entry():
    index = _FoldedMap({"Client_Id": 1, "CLIENT_ID": 2, "ClientId": 3})

    assert index.get_entry(_SimplePathSegment("Client_Id")).value == 1
    assert index.get_entry(_SimplePathSegment("CLIENT_ID")).value == 2
    assert index.get_entry(_SimplePathSegment("ClientId")).value == 3
    assert index.get_entry(_SimplePathSegment("client_id")) is None
    entry = index.get_entry(_SimplePathSegment("client_id", ignore_case=True))
    assert (entry.key, entry.value) == ("Client_Id", 1)


def test_update_preserves_matched_key_and_leaves_other_bucket_entries_unchanged():
    index = _FoldedMap({"Client_Id": 1, "ClientId": 2})

    actual_key = index.update_entry(
        _SimplePathSegment("CLIENT_ID", ignore_case=True), None
    )

    assert actual_key == "Client_Id"
    assert index.get_entry(_SimplePathSegment("Client_Id")).value is None
    assert index.get_entry(_SimplePathSegment("ClientId")).value == 2


def test_delete_preserves_colliding_entries_and_allows_reinsertion():
    index = _FoldedMap({"Client_Id": 1, "ClientId": 2})

    assert index.delete_entry("Client_Id") == "Client_Id"
    assert index.get_entry(_SimplePathSegment("Client_Id")) is None
    assert index.get_entry(_SimplePathSegment("ClientId")).value == 2
    assert index.delete_entry("ClientId") == "ClientId"
    assert index.get_bucket("CLIENT_ID") is None
    assert index.delete_entry("missing") is None

    assert index.update_entry("Client_Id", 3) == "Client_Id"
    assert index.get_entry(_SimplePathSegment("Client_Id")).value == 3


@pytest.mark.parametrize(
    "source",
    [
        {1: "integer", "1": "string"},
        {"1": "string", 1: "integer"},
    ],
)
def test_integer_and_string_keys_remain_distinct_during_update_and_delete(source):
    index = _FoldedMap(source)

    assert len(index.get_bucket("1")) == 2
    assert index.get_entry(_SimplePathSegment(1)).value == "integer"
    assert index.get_entry(_SimplePathSegment("1")).value == "string"

    assert index.update_entry(1, "updated") == 1
    assert index.get_entry(_SimplePathSegment(1)).value == "updated"
    assert index.get_entry(_SimplePathSegment("1")).value == "string"
    assert index.delete_entry(1) == 1
    assert index.get_entry(_SimplePathSegment(1)) is None
    assert index.get_entry(_SimplePathSegment("1")).value == "string"


@pytest.mark.parametrize("stored_key", ["01", "\u0661", "\uff11"])
def test_noncanonical_decimal_keys_are_not_aliases_of_ascii_integer_keys(
    stored_key,
):
    segment = _SimplePathSegment("1")
    index = _FoldedMap({stored_key: "value"})

    assert not segment.check(stored_key)
    assert index.get_entry(segment) is None
    entry = index.get_entry(_SimplePathSegment(stored_key))

    assert entry is not None
    assert (entry.key, entry.value) == (stored_key, "value")


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_canonical_numeric_mutation_does_not_touch_a_leading_zero_key(operation):
    index = _FoldedMap({"01": 7, "Other": 8})
    segment = _SimplePathSegment("1")

    if operation == "update":
        assert index.update_entry(segment, 9) == "1"
        assert index.get_entry(segment).value == 9
    else:
        assert index.delete_entry(segment) is None

    assert index.get_entry(_SimplePathSegment("01")).value == 7
    assert index.get_entry(_SimplePathSegment("Other")).value == 8


def test_unicode_casefold_collision_retains_source_order_after_delete_and_reinsert():
    index = _FoldedMap({"Straße": 1, "STRASSE": 2})
    segment = _SimplePathSegment("strasse", ignore_case=True)

    assert index.get_entry(segment).key == "Straße"
    assert index.delete_entry(_SimplePathSegment("Straße")) == "Straße"
    assert index.update_entry("Straße", 3) == "Straße"
    assert [(entry.key, entry.value) for entry in index.get_bucket(segment)] == [
        ("STRASSE", 2),
        ("Straße", 3),
    ]
    assert index.get_entry(segment).key == "STRASSE"
