# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar
from collections.abc import Sequence

from pydantic import BaseModel

from microsoft_agents.hosting.testing.core import ExpectBase

ModelT = TypeVar("ModelT", bound=dict | BaseModel)

def expect(items: ModelT | Sequence[ModelT]) -> ExpectBase[ModelT]:
    """Create an Expect instance for a collection of items.

    :param items: A Sequence of dicts or BaseModel instances. Can also be a single dict or BaseModel, which will be wrapped in a list.
    :return: An Expect instance for the provided items.
    """
    return ExpectBase(items)