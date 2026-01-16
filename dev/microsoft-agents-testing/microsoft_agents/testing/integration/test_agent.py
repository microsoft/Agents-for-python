from abc import ABC

from .application_runner import ApplicationRunner

class TestAgent(ABC):

    def get_runner(self) -> ApplicationRunner:
        pass