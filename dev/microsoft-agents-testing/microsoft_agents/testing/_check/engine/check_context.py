# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any

from .types import SafeObject

class CheckContext:

    def __init__(
        self,
        actual: SafeObject,
        baseline: Any,
    ):
        
        self.actual = actual
        self.baseline = baseline
        self.path = []
        self.root_actual = actual
        self.root_baseline = baseline

    def child(self, key: Any) -> CheckContext:

        child_ctx = CheckContext(
            actual=self.actual[key],
            baseline=self.baseline[key]
        )
        child_ctx.path = self.path + [key]
        child_ctx.root_actual = self.root_actual
        child_ctx.root_baseline = self.root_baseline
        return child_ctx