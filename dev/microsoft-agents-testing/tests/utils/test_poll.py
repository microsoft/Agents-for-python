# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the poll utility function."""

import asyncio

import pytest

from microsoft_agents.testing.utils import poll


class TestPoll:
    """Tests for the poll() function."""

    @pytest.mark.asyncio
    async def test_raises_for_negative_interval(self):
        """poll() raises ValueError when interval is negative."""
        with pytest.raises(ValueError, match="Interval must be a non-negative number"):
            await poll(lambda: True, timeout=1.0, interval=-0.1)

    @pytest.mark.asyncio
    async def test_raises_when_timeout_less_than_interval(self):
        """poll() raises ValueError when timeout is less than interval."""
        with pytest.raises(
            ValueError, match="Timeout must be greater than or equal to interval"
        ):
            await poll(lambda: True, timeout=0.05, interval=0.5)

    @pytest.mark.asyncio
    async def test_returns_when_condition_true_immediately(self):
        """poll() returns after a single condition check when it is True on the first call."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return True

        await poll(condition, timeout=1.0, interval=0.01)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_until_condition_becomes_true(self):
        """poll() keeps calling condition until it returns True."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        await poll(condition, timeout=1.0, interval=0.01)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_timeout_error_when_condition_never_true(self):
        """poll() raises TimeoutError when the condition never becomes True."""
        with pytest.raises(TimeoutError, match="Polling timed out"):
            await poll(lambda: False, timeout=0.05, interval=0.01)

    @pytest.mark.asyncio
    async def test_calls_condition_multiple_times_before_timeout(self):
        """poll() calls condition repeatedly, not just once, before timing out."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return False

        with pytest.raises(TimeoutError):
            await poll(condition, timeout=0.05, interval=0.01)

        assert call_count > 1

    @pytest.mark.asyncio
    async def test_accepts_zero_interval(self):
        """poll() accepts interval=0 (non-negative boundary value)."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 2

        await poll(condition, timeout=1.0, interval=0.0)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_default_interval_is_point_one(self):
        """poll() uses 0.1s as the default interval between checks."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 2

        loop = asyncio.get_event_loop()
        start = loop.time()
        await poll(condition, timeout=2.0)
        elapsed = loop.time() - start

        assert call_count == 2
        assert elapsed >= 0.1
