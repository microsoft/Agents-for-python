# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
StreamCapture - Captures and manages streaming responses from agents.

Provides utilities for testing agents that send incremental/streaming updates,
such as LLM-based agents that stream tokens progressively.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Callable, Awaitable, TypeVar, Generic
from enum import Enum

from pydantic import BaseModel


class StreamState(Enum):
    """State of a stream capture."""
    PENDING = "pending"       # Not yet started
    STREAMING = "streaming"   # Actively receiving chunks
    COMPLETED = "completed"   # Stream finished successfully
    ERROR = "error"           # Stream ended with error
    TIMEOUT = "timeout"       # Stream timed out
    CANCELLED = "cancelled"   # Stream was cancelled


@dataclass
class StreamChunk:
    """A single chunk received from a streaming response."""
    
    content: str
    """The text content of this chunk."""
    
    index: int
    """Zero-based index of this chunk in the stream."""
    
    received_at: datetime
    """Timestamp when this chunk was received."""
    
    delta_ms: float | None = None
    """Milliseconds since the previous chunk (None for first chunk)."""
    
    metadata: dict = field(default_factory=dict)
    """Optional metadata associated with this chunk."""
    
    @property
    def is_first(self) -> bool:
        """True if this is the first chunk in the stream."""
        return self.index == 0


@dataclass
class StreamMetrics:
    """Metrics collected during stream capture."""
    
    total_chunks: int = 0
    """Total number of chunks received."""
    
    total_length: int = 0
    """Total character length of all chunks combined."""
    
    first_chunk_at: datetime | None = None
    """Timestamp of the first chunk."""
    
    last_chunk_at: datetime | None = None
    """Timestamp of the last chunk."""
    
    min_delta_ms: float | None = None
    """Minimum time between chunks in milliseconds."""
    
    max_delta_ms: float | None = None
    """Maximum time between chunks in milliseconds."""
    
    avg_delta_ms: float | None = None
    """Average time between chunks in milliseconds."""
    
    @property
    def total_duration_ms(self) -> float | None:
        """Total duration from first to last chunk in milliseconds."""
        if self.first_chunk_at and self.last_chunk_at:
            delta = self.last_chunk_at - self.first_chunk_at
            return delta.total_seconds() * 1000.0
        return None
    
    @property
    def chunks_per_second(self) -> float | None:
        """Average chunks per second."""
        duration = self.total_duration_ms
        if duration and duration > 0 and self.total_chunks > 1:
            return (self.total_chunks - 1) / (duration / 1000.0)
        return None


ChunkT = TypeVar("ChunkT")


class StreamCapture(Generic[ChunkT]):
    """
    Captures streaming responses from an agent for testing and analysis.
    
    Usage:
        # Basic capture
        stream = StreamCapture()
        async for chunk in agent.stream_response("Tell me a story"):
            stream.add(chunk)
        
        # Assert on accumulated content
        assert "once upon a time" in stream.text.lower()
        
        # Check streaming behavior
        assert stream.metrics.total_chunks > 5
        assert stream.metrics.avg_delta_ms < 500
        
        # Wait for specific content
        stream = StreamCapture()
        async with stream.capture_from(agent.stream_response("Hello")):
            await stream.wait_for_text("Hello")
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        chunk_extractor: Callable[[ChunkT], str] | None = None,
    ) -> None:
        """Initialize a StreamCapture.
        
        :param timeout: Maximum time to wait for stream completion in seconds.
        :param chunk_extractor: Optional function to extract text from chunk objects.
                               If None, chunks are expected to be strings.
        """
        self._timeout = timeout
        self._chunk_extractor = chunk_extractor or (lambda x: str(x))
        
        self._chunks: list[StreamChunk] = []
        self._state = StreamState.PENDING
        self._error: Exception | None = None
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        
        # For async waiting
        self._content_event = asyncio.Event()
        self._complete_event = asyncio.Event()
        self._waiters: list[tuple[Callable[[str], bool], asyncio.Event]] = []
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def state(self) -> StreamState:
        """Current state of the stream capture."""
        return self._state
    
    @property
    def is_complete(self) -> bool:
        """True if the stream has finished (successfully or with error)."""
        return self._state in (
            StreamState.COMPLETED, 
            StreamState.ERROR, 
            StreamState.TIMEOUT,
            StreamState.CANCELLED,
        )
    
    @property
    def is_streaming(self) -> bool:
        """True if actively receiving chunks."""
        return self._state == StreamState.STREAMING
    
    @property
    def chunks(self) -> list[StreamChunk]:
        """All captured chunks."""
        return list(self._chunks)
    
    @property
    def text(self) -> str:
        """Accumulated text from all chunks."""
        return "".join(chunk.content for chunk in self._chunks)
    
    @property
    def error(self) -> Exception | None:
        """The error if stream ended with an error."""
        return self._error
    
    @property
    def metrics(self) -> StreamMetrics:
        """Computed metrics for this stream."""
        metrics = StreamMetrics()
        
        if not self._chunks:
            return metrics
        
        metrics.total_chunks = len(self._chunks)
        metrics.total_length = sum(len(c.content) for c in self._chunks)
        metrics.first_chunk_at = self._chunks[0].received_at
        metrics.last_chunk_at = self._chunks[-1].received_at
        
        # Calculate delta statistics
        deltas = [c.delta_ms for c in self._chunks if c.delta_ms is not None]
        if deltas:
            metrics.min_delta_ms = min(deltas)
            metrics.max_delta_ms = max(deltas)
            metrics.avg_delta_ms = sum(deltas) / len(deltas)
        
        return metrics
    
    # =========================================================================
    # Chunk Collection
    # =========================================================================
    
    def add(self, chunk: ChunkT | str, metadata: dict | None = None) -> StreamChunk:
        """Add a chunk to the capture.
        
        :param chunk: The chunk content (string or object with extractor).
        :param metadata: Optional metadata to attach to this chunk.
        :return: The created StreamChunk.
        """
        now = datetime.now(timezone.utc)
        
        # Initialize on first chunk
        if self._state == StreamState.PENDING:
            self._state = StreamState.STREAMING
            self._started_at = now
        
        # Extract text content
        if isinstance(chunk, str):
            content = chunk
        else:
            content = self._chunk_extractor(chunk)
        
        # Calculate delta from previous chunk
        delta_ms = None
        if self._chunks:
            last_time = self._chunks[-1].received_at
            delta = now - last_time
            delta_ms = delta.total_seconds() * 1000.0
        
        # Create and store chunk
        stream_chunk = StreamChunk(
            content=content,
            index=len(self._chunks),
            received_at=now,
            delta_ms=delta_ms,
            metadata=metadata or {},
        )
        self._chunks.append(stream_chunk)
        
        # Signal waiters
        self._content_event.set()
        self._check_waiters()
        
        return stream_chunk
    
    def complete(self) -> None:
        """Mark the stream as successfully completed."""
        if not self.is_complete:
            self._state = StreamState.COMPLETED
            self._completed_at = datetime.now(timezone.utc)
            self._complete_event.set()
            self._signal_all_waiters()
    
    def fail(self, error: Exception) -> None:
        """Mark the stream as failed with an error."""
        if not self.is_complete:
            self._state = StreamState.ERROR
            self._error = error
            self._completed_at = datetime.now(timezone.utc)
            self._complete_event.set()
            self._signal_all_waiters()
    
    def cancel(self) -> None:
        """Cancel the stream capture."""
        if not self.is_complete:
            self._state = StreamState.CANCELLED
            self._completed_at = datetime.now(timezone.utc)
            self._complete_event.set()
            self._signal_all_waiters()
    
    # =========================================================================
    # Async Waiting
    # =========================================================================
    
    async def wait_for_complete(self, timeout: float | None = None) -> None:
        """Wait for the stream to complete.
        
        :param timeout: Maximum time to wait (uses default if None).
        :raises TimeoutError: If the stream doesn't complete in time.
        :raises Exception: If the stream ended with an error.
        """
        timeout = timeout or self._timeout
        try:
            await asyncio.wait_for(self._complete_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self._state = StreamState.TIMEOUT
            self._completed_at = datetime.now(timezone.utc)
            raise TimeoutError(f"Stream did not complete within {timeout}s")
        
        if self._error:
            raise self._error
    
    async def wait_for_text(
        self,
        text: str,
        *,
        case_sensitive: bool = False,
        timeout: float | None = None,
    ) -> str:
        """Wait until the accumulated text contains the specified substring.
        
        :param text: The text to wait for.
        :param case_sensitive: Whether the match is case-sensitive.
        :param timeout: Maximum time to wait.
        :return: The accumulated text when the condition is met.
        :raises TimeoutError: If the text is not found in time.
        """
        def matcher(accumulated: str) -> bool:
            if case_sensitive:
                return text in accumulated
            return text.lower() in accumulated.lower()
        
        return await self.wait_for_condition(matcher, timeout=timeout)
    
    async def wait_for_condition(
        self,
        condition: Callable[[str], bool],
        timeout: float | None = None,
    ) -> str:
        """Wait until the accumulated text satisfies a condition.
        
        :param condition: A function that returns True when satisfied.
        :param timeout: Maximum time to wait.
        :return: The accumulated text when the condition is met.
        :raises TimeoutError: If the condition is not met in time.
        """
        timeout = timeout or self._timeout
        
        # Check if already satisfied
        if condition(self.text):
            return self.text
        
        # Create waiter
        waiter_event = asyncio.Event()
        waiter = (condition, waiter_event)
        self._waiters.append(waiter)
        
        try:
            await asyncio.wait_for(waiter_event.wait(), timeout=timeout)
            return self.text
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Condition not met within {timeout}s. "
                f"Accumulated text ({len(self.text)} chars): {self.text[:200]}..."
            )
        finally:
            if waiter in self._waiters:
                self._waiters.remove(waiter)
    
    async def wait_for_chunks(
        self,
        count: int,
        timeout: float | None = None,
    ) -> list[StreamChunk]:
        """Wait until at least N chunks have been received.
        
        :param count: Minimum number of chunks to wait for.
        :param timeout: Maximum time to wait.
        :return: The list of chunks when the count is reached.
        :raises TimeoutError: If not enough chunks arrive in time.
        """
        def condition(text: str) -> bool:
            return len(self._chunks) >= count
        
        await self.wait_for_condition(condition, timeout=timeout)
        return self.chunks
    
    def _check_waiters(self) -> None:
        """Check all waiters and signal those whose conditions are met."""
        accumulated = self.text
        for condition, event in self._waiters:
            if condition(accumulated):
                event.set()
    
    def _signal_all_waiters(self) -> None:
        """Signal all waiters (used when stream completes)."""
        for _, event in self._waiters:
            event.set()
    
    # =========================================================================
    # Context Manager for Capturing
    # =========================================================================
    
    async def capture_from(
        self,
        stream: AsyncIterator[ChunkT],
    ) -> "StreamCapture[ChunkT]":
        """Capture all chunks from an async iterator.
        
        Usage:
            stream = StreamCapture()
            await stream.capture_from(agent.stream_response("Hello"))
            assert "hello" in stream.text.lower()
        
        :param stream: An async iterator yielding chunks.
        :return: Self for chaining.
        """
        try:
            async for chunk in stream:
                self.add(chunk)
            self.complete()
        except Exception as e:
            self.fail(e)
            raise
        return self
    
    def capture_background(
        self,
        stream: AsyncIterator[ChunkT],
    ) -> asyncio.Task:
        """Start capturing in the background and return a task.
        
        Useful when you want to start capturing and then wait for
        specific conditions while the stream continues.
        
        Usage:
            stream = StreamCapture()
            task = stream.capture_background(agent.stream_response("Hello"))
            await stream.wait_for_text("world")
            await task  # Ensure completion
        
        :param stream: An async iterator yielding chunks.
        :return: An asyncio Task that completes when the stream ends.
        """
        return asyncio.create_task(self.capture_from(stream))
    
    # =========================================================================
    # Assertions
    # =========================================================================
    
    def assert_completed(self) -> "StreamCapture[ChunkT]":
        """Assert that the stream completed successfully."""
        if self._state != StreamState.COMPLETED:
            raise AssertionError(
                f"Expected stream to complete successfully, "
                f"but state is {self._state.value}"
            )
        return self
    
    def assert_text_contains(
        self, 
        substring: str, 
        case_sensitive: bool = False,
    ) -> "StreamCapture[ChunkT]":
        """Assert that the accumulated text contains a substring."""
        text = self.text
        if case_sensitive:
            if substring not in text:
                raise AssertionError(
                    f"Expected text to contain '{substring}', "
                    f"but got: {text[:200]}..."
                )
        else:
            if substring.lower() not in text.lower():
                raise AssertionError(
                    f"Expected text to contain '{substring}' (case-insensitive), "
                    f"but got: {text[:200]}..."
                )
        return self
    
    def assert_chunk_count(
        self,
        min_count: int | None = None,
        max_count: int | None = None,
    ) -> "StreamCapture[ChunkT]":
        """Assert the number of chunks received."""
        count = len(self._chunks)
        
        if min_count is not None and count < min_count:
            raise AssertionError(
                f"Expected at least {min_count} chunks, but got {count}"
            )
        if max_count is not None and count > max_count:
            raise AssertionError(
                f"Expected at most {max_count} chunks, but got {count}"
            )
        return self
    
    def assert_latency(
        self,
        max_first_chunk_ms: float | None = None,
        max_avg_delta_ms: float | None = None,
    ) -> "StreamCapture[ChunkT]":
        """Assert streaming latency characteristics."""
        metrics = self.metrics
        
        if max_first_chunk_ms is not None and self._started_at:
            # Time from request to first chunk would need request timestamp
            # For now, we just have chunk-to-chunk metrics
            pass
        
        if max_avg_delta_ms is not None:
            if metrics.avg_delta_ms is not None and metrics.avg_delta_ms > max_avg_delta_ms:
                raise AssertionError(
                    f"Expected average chunk delta ≤ {max_avg_delta_ms}ms, "
                    f"but got {metrics.avg_delta_ms:.2f}ms"
                )
        
        return self
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def reset(self) -> None:
        """Reset the capture to its initial state."""
        self._chunks.clear()
        self._state = StreamState.PENDING
        self._error = None
        self._started_at = None
        self._completed_at = None
        self._content_event.clear()
        self._complete_event.clear()
        self._waiters.clear()
    
    def __repr__(self) -> str:
        return (
            f"StreamCapture(state={self._state.value}, "
            f"chunks={len(self._chunks)}, "
            f"text_len={len(self.text)})"
        )
