# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import logging

from abc import ABC, abstractmethod
from contextlib import ExitStack
from typing import ContextManager
from venv import logger

from opentelemetry.trace import Span

logger = logging.getLogger(__name__)


class BaseSpanWrapper(ABC):
    """Wrapper around OTEL spans for SDK-specific telemetry"""

    def __init__(self):
        self._span: Span | None = None
        self._active: bool = False

        self._exit_stack = ExitStack()

    @property
    def otel_span(self) -> Span | None:
        """Returns the underlying OTEL span if it is active, or None if the span has not been started or has already ended. This can be used to access OTEL-specific functionality or attributes of the span when needed, while still providing a higher-level abstraction through the BaseSpanWrapper class."""
        if self._span is None:
            raise RuntimeError("BaseSpanWrapper has not been started yet")
        return self._span

    @property
    def active(self) -> bool:
        """Indicates whether the BaseSpanWrapper is currently active. This can be used to prevent operations on an inactive BaseSpanWrapper, and to check the BaseSpanWrapper's lifecycle state."""
        return self._active

    @abstractmethod
    def _start_span(self) -> ContextManager[Span]:
        """Abstract method that must be implemented by subclasses to define how the BaseSpanWrapper is started and what attributes are set on the BaseSpanWrapper. This method should return a context manager that yields the started BaseSpanWrapper, allowing the base BaseSpanWrapper class to manage the BaseSpanWrapper's lifecycle and ensure proper cleanup when the BaseSpanWrapper is ended."""
        raise NotImplementedError

    @staticmethod
    def _log_lifespan_error(desc: str) -> None:
        """Helper method to log a warning when an operation is attempted on an inactive BaseSpanWrapper. This can be used in methods that require an active BaseSpanWrapper to indicate potential misuse of the BaseSpanWrapper lifecycle."""
        logger.warning(
            "Attempting to perform an operation on an inactive BaseSpanWrapper. This may indicate a bug in the telemetry implementation or misuse of the BaseSpanWrapper lifecycle."
        )
        logger.warning("Description: %s", desc)

    def __enter__(self) -> BaseSpanWrapper:
        """Starts the BaseSpanWrapper and returns the BaseSpanWrapper instance for chaining. This method should check if the BaseSpanWrapper is already active and log a warning if an attempt is made to start an already active BaseSpanWrapper, to help identify potential issues with BaseSpanWrapper lifecycle management."""
        if self._active:
            BaseSpanWrapper._log_lifespan_error(
                "Attempting to start a BaseSpanWrapper that is already active."
            )

        self._span = self._exit_stack.enter_context(self._start_span())
        self._active = True

        return self

    def start(self) -> BaseSpanWrapper:
        """Starts the BaseSpanWrapper and returns the BaseSpanWrapper instance for chaining"""
        return self.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stops the BaseSpanWrapper if it is active, and logs a warning if an attempt is made to stop a BaseSpanWrapper that is not active. This ensures that BaseSpanWrappers are properly cleaned up and that potential issues with BaseSpanWrapper lifecycle management are logged for debugging purposes."""
        if self._active:
            self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
            self._span = None
            self._active = False
        else:
            BaseSpanWrapper._log_lifespan_error(
                "BaseSpanWrapper is not active and cannot be exited"
            )

    def end(self) -> None:
        """Stops the BaseSpanWrapper if it is active"""
        self.__exit__(None, None, None)
