from typing import Callable

class Predicate:

    def __init__(self, _base: dict | Callable | None = None, **kwargs) -> None:
        self._base = _base
        self._kwargs = kwargs