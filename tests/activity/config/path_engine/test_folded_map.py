# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity.config._engine._path._folded_map import (
    _FoldedMap,
    _get_folded_key,
    _ps,
)
from microsoft_agents.activity.config._engine._path.types import (
    _ExactPathSegment,
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

    assert index.get_entry(_ExactPathSegment("Client_Id")).value == 1
    assert index.get_entry(_ExactPathSegment("CLIENT_ID")).value == 2
    assert index.get_entry(_ExactPathSegment("ClientId")).value == 3
    assert index.get_entry(_ExactPathSegment("client_id")) is None
    entry = index.get_entry(_SimplePathSegment("client_id", ignore_case=True))
    assert (entry.key, entry.value) == ("Client_Id", 1)


def test_update_preserves_matched_key_and_leaves_other_bucket_entries_unchanged():
    index = _FoldedMap({"Client_Id": 1, "ClientId": 2})

    actual_key = index.update_entry(
        _SimplePathSegment("CLIENT_ID", ignore_case=True), None
    )

    assert actual_key == "Client_Id"
    assert index.get_entry(_ExactPathSegment("Client_Id")).value is None
    assert index.get_entry(_ExactPathSegment("ClientId")).value == 2


def test_delete_preserves_colliding_entries_and_allows_reinsertion():
    index = _FoldedMap({"Client_Id": 1, "ClientId": 2})

    assert index.delete_entry("Client_Id") == "Client_Id"
    assert index.get_entry(_ExactPathSegment("Client_Id")) is None
    assert index.get_entry(_ExactPathSegment("ClientId")).value == 2
    assert index.delete_entry("ClientId") == "ClientId"
    assert index.get_bucket("CLIENT_ID") is None
    assert index.delete_entry("missing") is None

    assert index.update_entry("Client_Id", 3) == "Client_Id"
    assert index.get_entry(_ExactPathSegment("Client_Id")).value == 3
