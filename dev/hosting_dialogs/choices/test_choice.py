# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List

import pytest

from microsoft_agents.hosting.dialogs.choices import Choice
from microsoft_agents.activity import CardAction


class TestChoice:
    def test_value_round_trips(self) -> None:
        choice = Choice()
        expected = "any"
        choice.value = expected
        assert expected is choice.value

    def test_action_round_trips(self) -> None:
        choice = Choice()
        expected = CardAction(type="imBack", title="Test Action")
        choice.action = expected
        assert expected is choice.action

    def test_synonyms_round_trips(self) -> None:
        choice = Choice()
        expected: List[str] = []
        choice.synonyms = expected
        assert expected is choice.synonyms
