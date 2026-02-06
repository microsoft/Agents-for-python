# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Describe - Generate human-readable descriptions of assertion results.

Provides utilities for creating meaningful error messages when assertions
fail, including details about which items failed and why.
"""

import inspect
from typing import Any, Callable

from .model_predicate import ModelPredicateResult
from .quantifier import (
    Quantifier,
    for_any,
    for_all,
    for_none,
    for_one,
)
from .utils import flatten


class Describe:
    """Generates human-readable descriptions of predicate evaluation results."""

    def __init__(self):
        pass

    def _count_summary(self, results: list[bool]) -> str:
        """Generate a count summary of true/false results."""
        true_count = sum(1 for r in results if r)
        total = len(results)
        return f"{true_count}/{total} items matched"

    def _indices_summary(self, results: list[bool], matched: bool = True) -> str:
        """Generate a summary of which indices matched or failed."""
        indices = [i for i, r in enumerate(results) if r == matched]
        if not indices:
            return "none"
        if len(indices) <= 5:
            return f"[{', '.join(str(i) for i in indices)}]"
        return f"[{', '.join(str(i) for i in indices[:5])}, ... +{len(indices) - 5} more]"

    def _describe_for_any(self, mpr: ModelPredicateResult, passed: bool) -> str:
        """Describe result for 'any' quantifier."""
        if passed:
            matched_indices = self._indices_summary(mpr.result_bools, matched=True)
            return f"✓ At least one item matched (indices: {matched_indices}). {self._count_summary(mpr.result_bools)}."
        else:
            return f"✗ Expected at least one item to match, but none did. {self._count_summary(mpr.result_bools)}."

    def _describe_for_all(self, mpr: ModelPredicateResult, passed: bool) -> str:
        """Describe result for 'all' quantifier."""
        if passed:
            return f"✓ All {len(mpr.result_bools)} items matched."
        else:
            failed_indices = self._indices_summary(mpr.result_bools, matched=False)
            return f"✗ Expected all items to match, but some failed (indices: {failed_indices}). {self._count_summary(mpr.result_bools)}."

    def _describe_for_none(self, mpr: ModelPredicateResult, passed: bool) -> str:
        """Describe result for 'none' quantifier."""
        if passed:
            return f"✓ No items matched (as expected). Checked {len(mpr.result_bools)} items."
        else:
            matched_indices = self._indices_summary(mpr.result_bools, matched=True)
            return f"✗ Expected no items to match, but some did (indices: {matched_indices}). {self._count_summary(mpr.result_bools)}."

    def _describe_for_one(self, mpr: ModelPredicateResult, passed: bool) -> str:
        """Describe result for 'exactly one' quantifier."""
        true_count = sum(1 for r in mpr.result_bools if r)
        if passed:
            matched_index = next(i for i, r in enumerate(mpr.result_bools) if r)
            return f"✓ Exactly one item matched (index: {matched_index}). Checked {len(mpr.result_bools)} items."
        else:
            if true_count == 0:
                return f"✗ Expected exactly one item to match, but none did. Checked {len(mpr.result_bools)} items."
            else:
                matched_indices = self._indices_summary(mpr.result_bools, matched=True)
                return f"✗ Expected exactly one item to match, but {true_count} matched (indices: {matched_indices})."

    def _describe_for_n(self, mpr: ModelPredicateResult, passed: bool, n: int) -> str:
        """Describe result for 'exactly n' quantifier."""
        true_count = sum(1 for r in mpr.result_bools if r)
        if passed:
            return f"✓ Exactly {n} items matched. {self._count_summary(mpr.result_bools)}."
        else:
            return f"✗ Expected exactly {n} items to match, but {true_count} matched. {self._count_summary(mpr.result_bools)}."

    def _describe_default(self, mpr: ModelPredicateResult, passed: bool, quantifier_name: str) -> str:
        """Describe result for unknown/custom quantifiers."""
        status = "✓ Passed" if passed else "✗ Failed"
        return f"{status} for quantifier '{quantifier_name}'. {self._count_summary(mpr.result_bools)}."

    def describe(self, mpr: ModelPredicateResult, quantifier: Quantifier) -> str:
        """Generate a human-readable description of the predicate evaluation result.
        
        :param mpr: The ModelPredicateResult containing evaluation results.
        :param quantifier: The quantifier function used for evaluation.
        :return: A descriptive string explaining the result.
        """
        passed = quantifier(mpr.result_bools)
        quantifier_name = getattr(quantifier, '__name__', str(quantifier))

        if quantifier is for_any:
            return self._describe_for_any(mpr, passed)
        elif quantifier is for_all:
            return self._describe_for_all(mpr, passed)
        elif quantifier is for_none:
            return self._describe_for_none(mpr, passed)
        elif quantifier is for_one:
            return self._describe_for_one(mpr, passed)
        else:
            return self._describe_default(mpr, passed, quantifier_name)

    def describe_failures(self, mpr: ModelPredicateResult) -> list[str]:
        """Generate detailed descriptions for each failed item.
        
        :param mpr: The ModelPredicateResult containing evaluation results.
        :return: A list of failure descriptions, one per failed item.
        """
        failures = []
        for i, (result_bool, result_dict) in enumerate(zip(mpr.result_bools, mpr.result_dicts)):
            if not result_bool:
                failed_keys = [k for k, v in flatten(result_dict).items() if not v]
                if failed_keys:
                    key_details = []
                    # Get the source for this specific item
                    item_source = mpr.source[i] if i < len(mpr.source) else {}
                    for key in failed_keys:
                        func = mpr.dict_transform.get(key)
                        
                        # Get actual value from source
                        actual_value = self._get_nested_value(item_source, key)
                        
                        if func and callable(func):
                            # Try to get the expected value from lambda defaults (_v=val)
                            expected_value = self._get_expected_value(func)
                            
                            try:
                                source_code = inspect.getsource(func)
                                if expected_value is not None:
                                    key_details.append(
                                        f"  {key}:\n"
                                        f"    source: {source_code.strip()}\n"
                                        f"    expected: {expected_value!r}\n"
                                        f"    actual: {actual_value!r}"
                                    )
                                else:
                                    key_details.append(
                                        f"  {key}:\n"
                                        f"    source: {source_code.strip()}\n"
                                        f"    actual: {actual_value!r}"
                                    )
                            except (OSError, TypeError):
                                if expected_value is not None:
                                    key_details.append(
                                        f"  {key}:\n"
                                        f"    source: <source unavailable>\n"
                                        f"    expected: {expected_value!r}\n"
                                        f"    actual: {actual_value!r}"
                                    )
                                else:
                                    key_details.append(
                                        f"  {key}:\n"
                                        f"    source: <source unavailable>\n"
                                        f"    actual: {actual_value!r}"
                                    )
                        else:
                            key_details.append(
                                f"  {key}:\n"
                                f"    source: <no function>\n"
                                f"    actual: {actual_value!r}"
                            )
                    failures.append(f"Item {i}: failed on keys {failed_keys}\n" + "\n".join(key_details))
                else:
                    failures.append(f"Item {i}: failed")
        return failures

    def _get_expected_value(self, func: Callable) -> Any:
        """Extract the expected value (_v) from a lambda's defaults.
        
        :param func: The callable function to inspect.
        :return: The expected value if found, None otherwise.
        """
        try:
            # Check function defaults for _v parameter
            if hasattr(func, '__defaults__') and func.__defaults__:
                # The _v=val pattern stores val in __defaults__
                return func.__defaults__[0]
        except (AttributeError, IndexError):
            pass
        return None

    def _get_nested_value(self, source: dict | list, key: str) -> Any:
        """Get a nested value from source using dot-notation key.
        
        :param source: The source dictionary or list.
        :param key: The dot-notation key (e.g., 'user.profile.name').
        :return: The value at the key path, or '<missing>' if not found.
        """
        if isinstance(source, list):
            # For lists, we can't use dot notation directly
            return source
        
        keys = key.split(".")
        current = source
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return "<missing>"
        return current
