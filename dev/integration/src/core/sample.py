from abc import ABC, abstractmethod

from .environment import Environment


class Sample(ABC):
    """Base class for all samples."""

    def __init__(self, environment: Environment, **kwargs):
        self.env = environment

    @abstractmethod
    async def init_app(self):
        """Initialize the application for the sample."""