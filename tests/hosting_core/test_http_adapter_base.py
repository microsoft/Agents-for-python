# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import AsyncMock, Mock

import pytest

from microsoft_agents.activity import Activity, DeliveryModes
from microsoft_agents.hosting.core import HttpAdapterBase, OutboundHostValidator
from microsoft_agents.hosting.core.authorization import ClaimsIdentity


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize(
    ("service_url", "claim", "matches"),
    [
        (
            "https://smba.trafficmanager.net/teams/",
            "HTTPS://SMBA.trafficmanager.net/other/",
            True,
        ),
        (
            "https://smba.trafficmanager.net:443/teams/",
            "https://smba.trafficmanager.net/other/",
            True,
        ),
        (
            "https://smba.trafficmanager.net/teams/",
            "https://smba.trafficmanager.net:443/other/",
            True,
        ),
        (
            "https://smba.trafficmanager.net/teams/",
            "http://smba.trafficmanager.net/teams/",
            False,
        ),
        (
            "https://smba.trafficmanager.net:444/teams/",
            "https://smba.trafficmanager.net/teams/",
            False,
        ),
        (
            "https://smba.trafficmanager.net/teams/",
            "https://smba.trafficmanager.net:444/teams/",
            False,
        ),
        (
            "https://smba.trafficmanager.net/teams/",
            "https://graph.microsoft.com/teams/",
            False,
        ),
        (
            "https://smba.trafficmanager.net/teams/",
            "not-a-url",
            False,
        ),
        ("https://smba.trafficmanager.net/teams/", None, True),
        ("http://localhost/api/", "http://localhost:80/claim/", True),
        ("http://localhost:3978/api/", "http://localhost:3979/claim/", False),
        ("http://localhost:3978/api/", "https://localhost:3978/claim/", False),
    ],
)
def test_service_url_claim_binds_origin_but_not_path(
    enabled, service_url, claim, matches, caplog
):
    adapter = HttpAdapterBase(
        channel_service_client_factory=Mock(),
        host_validator=OutboundHostValidator(
            enabled=enabled,
            hosts=["localhost"],
            allow_private_network_addresses=True,
            allow_http_for_loopback=True,
        ),
    )
    identity = ClaimsIdentity({"serviceurl": claim} if claim else {"aud": "app"})

    assert adapter._validate_service_url(
        identity, Activity(type="message", service_url=service_url)
    ) is (matches or not enabled)
    if not matches and not enabled:
        assert "host validator disabled" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("activity_type", "delivery_mode"),
    [
        ("message", DeliveryModes.normal),
        ("invoke", DeliveryModes.normal),
        ("message", DeliveryModes.expect_replies),
        ("message", DeliveryModes.stream),
    ],
)
@pytest.mark.parametrize(
    ("service_url", "claim"),
    [
        ("http://smba.trafficmanager.net/teams/", None),
        (
            "https://smba.trafficmanager.net/teams/",
            "http://smba.trafficmanager.net/teams/",
        ),
        (
            "https://smba.trafficmanager.net:444/teams/",
            "https://smba.trafficmanager.net/teams/",
        ),
    ],
)
async def test_invalid_service_url_is_rejected_before_activity_processing(
    activity_type, delivery_mode, service_url, claim
):
    adapter = HttpAdapterBase(
        channel_service_client_factory=Mock(),
        host_validator=OutboundHostValidator(enabled=True),
    )
    adapter.process_activity = AsyncMock()
    request = Mock()
    request.method = "POST"
    request.json = AsyncMock(
        return_value={
            "type": activity_type,
            "deliveryMode": delivery_mode,
            "conversation": {"id": "conversation-id"},
            "serviceUrl": service_url,
        }
    )
    request.get_claims_identity.return_value = ClaimsIdentity(
        {"serviceurl": claim} if claim else {"aud": "app"}
    )

    response = await adapter.process_request(request, Mock())

    assert response.status_code == 401
    adapter.process_activity.assert_not_awaited()
