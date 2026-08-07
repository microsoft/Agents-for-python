# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Generic, TypeVar

ParamsT = TypeVar("ParamsT")


@dataclass
class AdaptiveCardSearchParams:

    query_text: str
    dataset: str


@dataclass
class AdaptiveCardSearchResult:

    title: str
    value: str


@dataclass
class Query(Generic[ParamsT]):

    count: int
    skip: int
    parameters: ParamsT
