# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.core.authorization.connections.connections_map import (
    _ConnectionMap,
    _ConnectionMapItem,
)


@pytest.mark.parametrize("values", [None, [], {}])
def test_empty_connections_maps_are_falsy(values):
    connections_map = _ConnectionMap(values)

    assert not connections_map
    assert list(connections_map) == []


@pytest.mark.parametrize("shape", ["list", "indexed", "named"])
@pytest.mark.parametrize(
    "entry",
    [
        {"connection": "MCS", "service_url": "agentic", "audience": "api://mcs"},
        {"CONNECTION": "MCS", "SERVICE_URL": "agentic", "AUDIENCE": "api://mcs"},
        {"CONNECTION": "MCS", "SERVICEURL": "agentic", "AUDIENCE": "api://mcs"},
    ],
)
def test_supported_shapes_and_aliases_bind_identical_routes(shape, entry):
    entries = (
        [entry] if shape == "list" else {"0" if shape == "indexed" else "route": entry}
    )

    connections_map = _ConnectionMap(entries)

    assert connections_map
    assert list(connections_map) == [
        _ConnectionMapItem(
            service_url="agentic", audience="api://mcs", connection="MCS"
        )
    ]
    assert connections_map["MCS"] == list(connections_map)[0]


def test_typed_items_are_reused_in_order():
    first = _ConnectionMapItem(service_url="first", connection="FIRST")
    second = _ConnectionMapItem(service_url="*", connection="SECOND")

    connections_map = _ConnectionMap([first, second])

    assert list(connections_map) == [first, second]
    assert connections_map["FIRST"] is first


def test_missing_connection_raises_key_error():
    with pytest.raises(KeyError, match="MISSING"):
        _ConnectionMap([])["MISSING"]


@pytest.mark.parametrize("entry", [None, "invalid", 3])
def test_malformed_route_entries_are_rejected(entry):
    with pytest.raises(ValueError, match="Expected dict"):
        _ConnectionMap({"route": entry})
