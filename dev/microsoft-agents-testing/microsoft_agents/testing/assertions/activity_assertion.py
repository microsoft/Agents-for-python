from typing import Optional

from microsoft_agents.activity import Activity

from .select_activity import select_activities
from .check_activity import check_activity_verbose
from .type_defs import (
    AssertionQuantifier,
    AssertionErrorData
)

class ActivityAssertion:

    def __init__(self, config: dict) -> None:
        """Initializes the ActivityAssertion with the given configuration.
        
        :param config: The configuration dictionary containing quantifier, selector, and assertion.
        """
        quantifier_name = config.get("quantifier", AssertionQuantifier.ALL)
        self._quantifier = AssertionQuantifier(quantifier_name)

        self._selector = config.get("selector", {})
        self._assertion = config.get("assertion", {})

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
        
        activities = select_activities(activities, self._selector)

        count = 0
        for activity in activities:
            res, assertion_error_data = check_activity_verbose(activity, self._assertion)
            if self._quantifier == AssertionQuantifier.ALL and not res:
                return False, f"Activity did not match the assertion: {activity}\nError: {assertion_error_data}"
            if self._quantifier == AssertionQuantifier.NONE and res:
                return False, f"Activity matched the assertion when none were expected: {activity}"
            count += 1

        passes = True
        if self._quantifier == AssertionQuantifier.ONE and count != 1:
            return False, f"Expected exactly one activity to match the assertion, but found {count}."

        return passes, None