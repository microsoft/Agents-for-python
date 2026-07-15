# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass


@dataclass
class SortedValue:
    """A value that can be sorted and still refer to its original position with a source array.

    value: the value that will be sorted.
    index: the value's original position within its unsorted array.
    """

    value: str
    index: int
