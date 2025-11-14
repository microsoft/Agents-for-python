# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional

from microsoft_agents.activity import Activity

from .check_activity import check_activity_verbose
from .selector import Selector
from .type_defs import AssertionQuantifier, AssertionErrorData


class ActivityAssertion:
    """Class for asserting activities based on a selector and assertion criteria."""

    _selector: Selector
    _quantifier: AssertionQuantifier
    _assertion: dict | Activity

    def __init__(
        self,
        assertion: dict | Activity | None = None,
        selector: Selector | None = None,
        quantifier: AssertionQuantifier = AssertionQuantifier.ALL,
    ) -> None:
        """Initializes the ActivityAssertion with the given configuration.

        :param config: The configuration dictionary containing quantifier, selector, and assertion.
        """

        self._assertion = assertion or {}
        self._selector = selector or Selector()
        self._quantifier = quantifier

    @staticmethod
    def _combine_assertion_errors(errors: list[AssertionErrorData]) -> str:
        """Combines multiple assertion errors into a single string representation.

        :param errors: The list of assertion errors to be combined.
        :return: A string representation of the combined assertion errors.
        """
        return "\n".join(str(error) for error in errors)

    def check(self, activities: list[Activity]) -> tuple[bool, Optional[str]]:
        """Asserts that the given activities match the assertion criteria.

        :param activities: The list of activities to be tested.
        :return: A tuple containing a boolean indicating if the assertion passed and an optional error message.
        """

        activities = self._selector(activities)

        count = 0
        for activity in activities:
            res, assertion_error_data = check_activity_verbose(
                activity, self._assertion
            )
            if self._quantifier == AssertionQuantifier.ALL and not res:
                return (
                    False,
                    f"Activity did not match the assertion: {activity}\nError: {assertion_error_data}",
                )
            if self._quantifier == AssertionQuantifier.NONE and res:
                return (
                    False,
                    f"Activity matched the assertion when none were expected: {activity}",
                )
            if res:
                count += 1

        passes = True
        if self._quantifier == AssertionQuantifier.ONE and count != 1:
            return (
                False,
                f"Expected exactly one activity to match the assertion, but found {count}.",
            )

        return passes, None

    def __call__(self, activities: list[Activity]) -> tuple[bool, Optional[str]]:
        """Allows the ActivityAssertion instance to be called directly.

        :param activities: The list of activities to be tested.
        :return: A tuple containing a boolean indicating if the assertion passed and an optional error message.
        """
        return self.check(activities)

    @staticmethod
    def from_config(config: dict) -> ActivityAssertion:
        """Creates an ActivityAssertion instance from a configuration dictionary.

        :param config: The configuration dictionary containing quantifier, selector, and assertion.
        :return: An ActivityAssertion instance.
        """
        assertion = config.get("assertion", {})
        selector = Selector.from_config(config.get("selector", {}))
        quantifier = AssertionQuantifier.from_config(config.get("quantifier", "all"))

        return ActivityAssertion(
            assertion=assertion,
            selector=selector,
            quantifier=quantifier,
        )
