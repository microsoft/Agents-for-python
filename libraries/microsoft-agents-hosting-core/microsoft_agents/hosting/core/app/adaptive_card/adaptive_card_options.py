# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass


@dataclass
class AdaptiveCardOptions:

    action_submit_filter: str | None = None
