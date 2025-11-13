from typing import Optional

from microsoft_agents.activity import Activity

from .select_activity import select_activities
from .type_defs import (
    AssertionQuantifier,
    SelectorQuantifier,
    FieldAssertionType,
    AssertionErrorData
)

class ActivityAssertion:

    def __init__(self, config: dict) -> None:
        quantifier_name = config.get("quantifier", AssertionQuantifier.ALL)
        self._quantifier = AssertionQuantifier(quantifier_name)

        self._selector = config.get("selector", {})
        self._assertion = config.get("assertion", {})

    def check(self, activities: list[Activity]) -> tuple[bool, list[AssertionErrorData]]:
        
        activities = select_activities(activities, self._selector)

        invert = self._quantifier == AssertionQuantifier.NONE

        count = 0
        assertion_error_data_list: list[AssertionErrorData] = []
        for activity in activities:
            res, assertion_error_data = check_activity_verbose(activity, self._assertion, invert=invert)
            if self._quantifier == AssertionQuantifier.ALL and not res:
                return False, assertion_error_data
            if self._quantifier == AssertionQuantifier.ANY and res:
                count += 1
        
        if self._quantifier == AssertionQuantifier.ANY:
            return count > 0, assertion_error_data_list
        if self._quantifier == AssertionQuantifier.ONE:
            return count == 1, assertion_error_data_list
        if self._quantifier == AssertionQuantifier.NONE:
            return count == 0, assertion_error_data_list
        

        



    def assert(self, activities: list[Activity]) -> None:
        res, assertion_error_data = self.check(activities)
        assertion_error_message = "\n".join(str(err) for err in assertion_error_data)
        assert res, assertion_error_message