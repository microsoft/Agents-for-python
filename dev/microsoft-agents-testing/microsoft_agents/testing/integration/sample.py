# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod

from .environment import Environment


class Sample(ABC):
    """Base class for all samples."""

    def __init__(self, environment: Environment, **kwargs):
        self.env = environment

    @classmethod
    async def get_config(cls) -> dict:
        """Retrieve the configuration for the sample."""
        return {}

    @abstractmethod
    async def init_app(self):
        """Initialize the application for the sample."""
