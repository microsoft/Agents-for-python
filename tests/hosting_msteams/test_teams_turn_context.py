# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsTurnContext helpers that can be exercised without a live adapter."""

from types import SimpleNamespace

import pytest

from .helpers import is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_agents.activity import (
        Activity,
        ActivityTreatmentTypes,
        Entity,
        ResourceResponse,
    )
    from microsoft_teams.api import ApiClient

    from microsoft_agents.hosting.core import TurnContext
    from microsoft_agents.hosting.msteams import TeamsTurnContext


class _StubAdapter:
    async def send_activities(self, context, activities):
        return [ResourceResponse()] * len(activities)


class TestMakeTargetedActivity:
    """``_make_targeted_activity`` mutates the supplied activity in place (returns
    None) by appending a TARGETED activity-treatment entity."""

    def test_appends_targeted_treatment_when_no_entities(self):
        activity = Activity(type="message")
        result = TeamsTurnContext._make_targeted_activity(activity)
        assert result is None
        assert len(activity.entities) == 1
        assert activity.entities[0].treatment == ActivityTreatmentTypes.TARGETED

    def test_preserves_existing_entities(self):
        activity = Activity(type="message", entities=[Entity(type="mention")])
        TeamsTurnContext._make_targeted_activity(activity)
        assert len(activity.entities) == 2
        assert activity.entities[0].type == "mention"
        assert activity.entities[1].treatment == ActivityTreatmentTypes.TARGETED

    def test_each_call_appends_another_treatment(self):
        # The helper is not idempotent: repeated calls accumulate treatments
        # (see BUGS.md #4). This pins the current behaviour.
        activity = Activity(type="message")
        TeamsTurnContext._make_targeted_activity(activity)
        TeamsTurnContext._make_targeted_activity(activity)
        treatments = [
            e
            for e in activity.entities
            if getattr(e, "treatment", None) == ActivityTreatmentTypes.TARGETED
        ]
        assert len(treatments) == 2


class TestTeamsApiClient:

    def test_api_client_returns_cached_client(self):
        activity = Activity(
            type="message",
            channel_id="msteams",
            service_url="https://smba.trafficmanager.net/teams/",
        )
        context = TurnContext(_StubAdapter(), activity)
        client = object.__new__(ApiClient)
        context.services.set(ApiClient, client)

        teams_context = TeamsTurnContext(
            context, SimpleNamespace(connection_manager=object())
        )

        assert teams_context.api_client is client
