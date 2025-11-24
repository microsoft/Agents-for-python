# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional

from microsoft_agents.activity import AgentsModel

from .check_model import check_model_verbose
from .selector import Selector
from .type_defs import AssertionQuantifier, AssertionErrorData

class ModelAssertion:
    """Class for asserting activities based on a selector and assertion criteria."""

    _selector: Selector
    _quantifier: AssertionQuantifier
    _assertion: dict | AgentsModel

    def __init__(
        self,
        assertion: dict | None = None,
        selector: Selector | None = None,
        quantifier: AssertionQuantifier = AssertionQuantifier.ALL,
    ) -> None:
        """Initializes the ModelAssertion with the given configuration.

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

    def check(self, items: list[dict]) -> tuple[bool, Optional[str]]:
        """Asserts that the given items match the assertion criteria.

        :param items: The list of items to be tested.
        :return: A tuple containing a boolean indicating if the assertion passed and an optional error message.
        """

        items = self._selector(items)

        count = 0
        for item in items:
            res, assertion_error_data = check_model_verbose(
                item, self._assertion
            )
            if self._quantifier == AssertionQuantifier.ALL and not res:
                return (
                    False,
                    f"Item did not match the assertion: {item}\nError: {assertion_error_data}",
                )
            if self._quantifier == AssertionQuantifier.NONE and res:
                return (
                    False,
                    f"Item matched the assertion when none were expected: {item}",
                )
            if res:
                count += 1

        passes = True
        if self._quantifier == AssertionQuantifier.ONE and count != 1:
            return (
                False,
                f"Expected exactly one item to match the assertion, but found {count}.",
            )

        return passes, None

    def __call__(self, items: list[dict]) -> None:
        """Allows the ModelAssertion instance to be called directly.

        :param items: The list of items to be tested.
        :return: A tuple containing a boolean indicating if the assertion passed and an optional error message.
        """
        passes, error = self.check(items)
        assert passes, error

    @staticmethod
    def from_config(config: dict) -> ModelAssertion:
        """Creates a ModelAssertion instance from a configuration dictionary.

        :param config: The configuration dictionary containing quantifier, selector, and assertion.
        :return: A ModelAssertion instance.
        """
        assertion = config.get("assertion", {})
        selector = Selector.from_config(config.get("selector", {}))
        quantifier = AssertionQuantifier.from_config(config.get("quantifier", "all"))

        return ModelAssertion(
            assertion=assertion,
            selector=selector,
            quantifier=quantifier,
        )
