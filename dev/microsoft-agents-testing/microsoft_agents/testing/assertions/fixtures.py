from typing import Any

from .assertion_context import AssertionContext

from .types import DynamicObject, Unset

class Fixtures:

    @staticmethod
    def exists():
        return lambda actual: actual is not Unset

    @staticmethod
    def not_exists():
        return lambda actual: actual is Unset

    