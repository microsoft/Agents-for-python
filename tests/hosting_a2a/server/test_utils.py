# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from a2a.types import AgentInterface
from a2a.utils.constants import TransportProtocol

from microsoft_agents.hosting.a2a.server._utils import _get_interface_route_path


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/a2a", "/a2a"),
        ("https://example.com/a2a", "/a2a"),
        ("https://example.com", "/"),
    ],
)
def test_get_interface_route_path(url, expected):
    interface = AgentInterface(
        url=url,
        protocol_binding=TransportProtocol.JSONRPC,
    )

    assert _get_interface_route_path(interface) == expected
