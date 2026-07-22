# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime

from microsoft_agents.testing.core import Exchange


def _exchange_sort_key(exchange: Exchange) -> tuple:
    """Sort key for exchanges by request timestamp.

    Returns a tuple to handle naive vs aware datetime comparisons.
    """
    dt = exchange.request_at
    if dt is None:
        dt = exchange.response_at
    if dt is None:
        # Use min datetime for None values
        return (datetime.min,)
    # Convert to naive for consistent comparison
    naive_dt = dt.replace(tzinfo=None) if dt.tzinfo else dt
    return (naive_dt,)


def _format_timestamp(dt: datetime | None) -> str:
    """Format a datetime for display."""
    if dt is None:
        return "??:??.???"
    return dt.strftime("%H:%M:%S.%f")[:-3]
