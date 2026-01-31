# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

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
                    failures.append(f"Item {i}: failed on keys {failed_keys}")
                else:
                    failures.append(f"Item {i}: failed")
        return failures
