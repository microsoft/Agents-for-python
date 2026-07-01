# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for internal helpers: the Teams API client accessor and error resources."""

import pytest

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_teams.api import ApiClient

    from microsoft_agents.hosting.msteams._teams_api_client import (
        _TEAMS_API_CLIENT_KEY,
        _get_teams_api_client,
    )
    from microsoft_agents.hosting.msteams.errors.error_resources import (
        TeamsErrorResources,
    )


class _FakeContext:
    """Minimal stand-in exposing only the ``turn_state`` dict the accessor reads."""

    def __init__(self, turn_state):
        self.turn_state = turn_state


class TestGetTeamsApiClient:

    def test_returns_cached_api_client(self):
        client = ApiClient("https://smba.trafficmanager.net/teams/")
        ctx = _FakeContext({_TEAMS_API_CLIENT_KEY: client})
        assert _get_teams_api_client(ctx) is client

    def test_raises_when_missing(self):
        ctx = _FakeContext({})
        with pytest.raises(ValueError, match="Teams API client"):
            _get_teams_api_client(ctx)

    def test_raises_when_wrong_type(self):
        ctx = _FakeContext({_TEAMS_API_CLIENT_KEY: object()})
        with pytest.raises(ValueError, match="Teams API client"):
            _get_teams_api_client(ctx)


class TestTeamsErrorResources:

    def _error_messages(self):
        return [
            value
            for name, value in vars(TeamsErrorResources).items()
            if not name.startswith("_")
        ]

    def test_error_codes_are_unique(self):
        codes = [msg.error_code for msg in self._error_messages()]
        assert len(codes) == len(set(codes))

    def test_error_codes_within_reserved_range(self):
        # The module documents the reserved range as -62000 to -62999.
        for msg in self._error_messages():
            assert -62999 <= msg.error_code <= -62000
