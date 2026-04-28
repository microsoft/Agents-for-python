# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.dialogs.choices import ChoiceFactoryOptions


class TestChoiceFactoryOptions:
    def test_inline_separator_round_trips(self) -> None:
        choice_factor_options = ChoiceFactoryOptions()
        expected = ", "
        choice_factor_options.inline_separator = expected
        assert expected == choice_factor_options.inline_separator

    def test_inline_or_round_trips(self) -> None:
        choice_factor_options = ChoiceFactoryOptions()
        expected = " or "
        choice_factor_options.inline_or = expected
        assert expected == choice_factor_options.inline_or

    def test_inline_or_more_round_trips(self) -> None:
        choice_factor_options = ChoiceFactoryOptions()
        expected = ", or "
        choice_factor_options.inline_or_more = expected
        assert expected == choice_factor_options.inline_or_more

    def test_include_numbers_round_trips(self) -> None:
        choice_factor_options = ChoiceFactoryOptions()
        expected = True
        choice_factor_options.include_numbers = expected
        assert expected == choice_factor_options.include_numbers
