# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""ModelPredicate - Evaluate predicates against model collections.

Provides the core predicate evaluation logic used by Expect and Select
to match items against specified criteria.
"""

from __future__ import annotations

from typing import Any, Callable, cast, Sequence
from dataclasses import dataclass

from pydantic import BaseModel

from .transform import DictionaryTransform, ModelTransform


@dataclass
class ModelPredicateResult:
    """Result of evaluating a predicate against a list of models.

    Contains the source data, the transformation applied, and per-item
    boolean results indicating which items matched the predicate.

    Attributes:
        source: The original list of dictionaries that were evaluated.
        dict_transform: The transformation mapping that was applied.
        result_bools: Boolean results per item (True = matched).
        result_dicts: Detailed results per item showing which fields matched.
    """

    source: Sequence[dict]
    dict_transform: dict
    result_bools: list[bool]
    result_dicts: list[dict]

    def __init__(
        self,
        source: Sequence[dict | BaseModel],
        dict_transform: dict,
        result_dicts: list[dict],
    ) -> None:
        if isinstance(source, Sequence) and source and isinstance(source[0], BaseModel):
            source = cast(Sequence[BaseModel], source)
            self.source = cast(
                Sequence[dict],
                [s.model_dump(exclude_unset=True, mode="json") for s in source],
            )
        else:
            self.source = cast(Sequence[dict], source)
        self.dict_transform = dict_transform
        self.result_dicts = result_dicts
        predicate_paths = list(self.dict_transform.keys())
        self.result_bools = [
            self._truthy(d, predicate_paths=predicate_paths) for d in self.result_dicts
        ]

    def _truthy(
        self, result: dict | Sequence, predicate_paths: Sequence[str] | None = None
    ) -> bool:

        if predicate_paths:
            return all(bool(self._get_path(result, path)) for path in predicate_paths)

        res: list[bool] = []

        if isinstance(result, dict):
            iterable = result.values()
        else:
            iterable = result

        for val in iterable:
            if isinstance(val, (dict, list)):
                res.append(self._truthy(val))
            else:
                res.append(bool(val))

        return all(res)

    def _get_path(self, result: dict | Sequence, path: str) -> Any:
        if isinstance(result, dict) and path in result:
            return result[path]

        current: Any = result
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]

        return current


class ModelPredicate:
    """Evaluates predicates against models to produce boolean results.

    Wraps a DictionaryTransform to evaluate it against one or more models,
    producing a ModelPredicateResult with per-item match information.
    """

    def __init__(self, dict_transform: DictionaryTransform) -> None:
        self._dt = dict_transform
        self._transform = ModelTransform(dict_transform)

    def eval(
        self, source: dict | BaseModel | Sequence[BaseModel | dict]
    ) -> ModelPredicateResult:
        """Evaluate the predicate against one or more models.

        :param source: A single model or a list of models to evaluate.
        :return: A ModelPredicateResult with per-item match results.
        """
        if not isinstance(source, Sequence):
            source = cast(Sequence[dict] | Sequence[BaseModel], [source])
        res = self._transform.eval(source)
        return ModelPredicateResult(source, self._dt.map, res)

    @staticmethod
    def from_args(
        arg: dict | Callable | None | ModelPredicate, **kwargs
    ) -> ModelPredicate:
        """Create a ModelPredicate from flexible argument types.

        Accepts an existing ModelPredicate, a dictionary, a callable,
        or None combined with keyword arguments.

        :param arg: A predicate source (dict, callable, ModelPredicate, or None).
        :param kwargs: Additional field criteria.
        :return: A ModelPredicate instance.
        """
        if isinstance(arg, ModelPredicate):
            return arg

        return ModelPredicate(DictionaryTransform.from_args(arg, **kwargs))
