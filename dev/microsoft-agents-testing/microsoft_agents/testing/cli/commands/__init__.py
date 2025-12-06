from click import Command

from .benchmark import benchmark
from .ddt import ddt
from .post import post
from .test_auth import test_auth

COMMAND_LIST: list[Command] = [
    benchmark,
    ddt,
    post,
    test_auth,
]

__all__ = [
    "COMMAND_LIST",
]
