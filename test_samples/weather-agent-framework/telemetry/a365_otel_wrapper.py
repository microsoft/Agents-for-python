# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Azure 365 observability wrapper for agent operations.

Python port of A365OtelWrapper.cs from sample-agent/telemetry.

The C# original depends on the internal
``Microsoft.Agents.A365.Observability`` packages which are .NET-only.
This Python port preserves the observable contract:

1. Resolve the tenant ID and agent ID from the current turn activity.
2. Propagate them as `OpenTelemetry baggage
   <https://opentelemetry.io/docs/concepts/signals/baggage/>`_ so that
   downstream services can consume the context.
3. Delegate to :func:`~telemetry.agent_metrics.invoke_observed_agent_operation`
   for span creation and metric recording.

The token-cache observability hook (``RegisterObservability``) present in the
C# wrapper has no equivalent in Python and is omitted.
"""

import logging
import uuid
from typing import Awaitable, Callable

from opentelemetry import baggage
from opentelemetry import context as otel_context

from .agent_metrics import invoke_observed_agent_operation

logger = logging.getLogger(__name__)

_EMPTY_GUID = str(uuid.UUID(int=0))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def invoke_observed_agent_operation_with_context(
    operation_name: str,
    turn_context,
    turn_state,
    func: Callable[[], Awaitable[None]],
) -> None:
    """Wrap an agent operation with A365 observability baggage context.

    Equivalent to ``A365OtelWrapper.InvokeObservedAgentOperation()`` in C#.

    Resolves the tenant ID and agent ID from the activity, sets them as
    OpenTelemetry baggage (equivalent to the C# ``BaggageBuilder``), then
    delegates to :func:`~telemetry.agent_metrics.invoke_observed_agent_operation`
    for span management and metric recording.

    Args:
        operation_name: Human-readable name of the operation / handler.
        turn_context: The current :class:`TurnContext`.
        turn_state: The current :class:`TurnState` (kept for API parity with
            the C# version; auth resolution is not performed here).
        func: Async function containing the agent logic to execute.
    """
    agent_id, tenant_id = _resolve_tenant_and_agent_id(turn_context)

    async def _with_baggage():
        # Set tenant.id and agent.id as baggage — equivalent to BaggageBuilder
        # in C#, which adds these values to the W3C baggage header so that
        # downstream services can read them.
        ctx = baggage.set_baggage("tenant.id", tenant_id)
        ctx = baggage.set_baggage("agent.id", agent_id, context=ctx)
        token = otel_context.attach(ctx)
        try:
            await func()
        finally:
            otel_context.detach(token)

    await invoke_observed_agent_operation(operation_name, turn_context, _with_baggage)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_tenant_and_agent_id(turn_context) -> tuple[str, str]:
    """Extract tenant and agent IDs from the turn activity.

    Equivalent to ``ResolveTenantAndAgentId()`` in C#.

    The C# version calls into M365 auth helpers
    (``GetAgenticInstanceId`` / ``ResolveAgentIdentity``) that are not
    available in Python.  This implementation derives the values directly
    from the activity fields that carry the same semantics:

    * **agent_id** — the ``recipient.id`` of the activity (the bot/agent
      identity that received the message).
    * **tenant_id** — ``conversation.tenantId`` or ``recipient.tenantId``,
      matching the fields inspected by the C# helper.

    Falls back to ``00000000-0000-0000-0000-000000000000`` (Guid.Empty) for
    any value that cannot be resolved, matching C# behaviour.

    Args:
        turn_context: The current :class:`TurnContext`.

    Returns:
        ``(agent_id, tenant_id)`` as strings.
    """
    activity = getattr(turn_context, "activity", None)
    if activity is None:
        return _EMPTY_GUID, _EMPTY_GUID

    # Agent ID — use recipient identity (the agent/bot that received the turn)
    recipient = getattr(activity, "recipient", None)
    agent_id = str(getattr(recipient, "id", None) or _EMPTY_GUID)

    # Tenant ID — prefer conversation.tenantId, then recipient.tenantId
    conversation = getattr(activity, "conversation", None)
    tenant_id = (
        getattr(conversation, "tenant_id", None)
        or getattr(recipient, "tenant_id", None)
        or _EMPTY_GUID
    )
    tenant_id = str(tenant_id)

    return agent_id, tenant_id
