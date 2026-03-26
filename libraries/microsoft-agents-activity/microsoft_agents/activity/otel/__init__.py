from __future__ import annotations

import functools
import logging
import types
from typing import Any, Collection, Literal


class AgentMetrics:

    tracer: Tracer


class AgentsSDKInstrumentor(BaseInstrumentor):
    """An OpenTelemetry Instrumentor for the Microsoft Agents SDK."""

    def _instrument(self, **kwargs: Any) -> None:
        """Instruments the Microsoft Agents SDK."""
        try:
            import microsoft_agents.activity.otel._agent_activity_tracing
        except ImportError as exc:
            logging.warning(
                "Failed to import Microsoft Agents SDK instrumentation module: %s",
                exc,
            )

    def _uninstrument(self, **kwargs: Any) -> None:
        """Uninstruments the Microsoft Agents SDK."""
        # No uninstrumentation logic needed for this instrumentation
        pass
