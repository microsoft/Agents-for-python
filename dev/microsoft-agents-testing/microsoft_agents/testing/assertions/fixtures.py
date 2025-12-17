from .types import Unset, FutureVar

class Fixtures:

    actual = FutureVar("actual")
    expected = FutureVar("expected")

    @staticmethod
    def exists(actual):
        return actual is not Unset

    @staticmethod
    def not_exists(actual):
        return actual is Unset

    @staticmethod
    def first(actual):
        return actual[0]
    
    @staticmethod
    def last(actual):
        return actual[-1]