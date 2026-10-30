# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.core.authorization.connections.connections_map import (
    _ConnectionMap,
)


@pytest.mark.parametrize("items", [None, [], {}])
def test_empty_maps_disable_routing(items):
    assert not _ConnectionMap(items)


@pytest.mark.parametrize("items", ["invalid", [None], {"rule": "invalid"}])
def test_invalid_map_shapes_raise(items):
    with pytest.raises(TypeError, match="mapping"):
        _ConnectionMap(items)


def test_map_preserves_order_and_binds_environment_aliases():
    rules = _ConnectionMap(
        {
            "first": {
                "SERVICEURL": "example",
                "AUDIENCE": "client",
                "CONNECTION": "OTHER",
            },
            "second": {"connection": "SERVICE_CONNECTION"},
        }
    )
    first, second = rules
    assert (first.service_url, first.audience, first.connection) == (
        "example",
        "client",
        "OTHER",
    )
    assert (second.service_url, second.audience, second.connection) == (
        "",
        "",
        "SERVICE_CONNECTION",
    )
