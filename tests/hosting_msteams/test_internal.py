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
    from microsoft_agents.hosting.msteams.errors.error_resources import (
        TeamsErrorResources,
    )


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
