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
4. Cache the observability token per-turn using the activity-derived IDs,
   equivalent to ``agentTokenCache.RegisterObservability()`` in C#.
"""

import logging
import uuid
from typing import Awaitable, Callable, Optional

from opentelemetry import baggage
from opentelemetry import context as otel_context

from microsoft_agents.hosting.core import AccessTokenProviderBase

from .agent_metrics import invoke_observed_agent_operation
from .token_cache import cache_agentic_token

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
    msal_auth: Optional[AccessTokenProviderBase] = None,
) -> None:
    """Wrap an agent operation with A365 observability baggage context.

    Equivalent to ``A365OtelWrapper.InvokeObservedAgentOperation()`` in C#.

    Resolves the tenant ID and agent ID from the activity, sets them as
    OpenTelemetry baggage (equivalent to the C# ``BaggageBuilder``), caches
    the observability token per-turn when ``msal_auth`` is provided (equivalent
    to ``agentTokenCache.RegisterObservability()``), then delegates to
    :func:`~telemetry.agent_metrics.invoke_observed_agent_operation` for span
    management and metric recording.

    Args:
        operation_name: Human-readable name of the operation / handler.
        turn_context: The current :class:`TurnContext`.
        turn_state: The current :class:`TurnState`.
        func: Async function containing the agent logic to execute.
        msal_auth: Optional MSAL authentication provider used to fetch and
            cache the observability token for the activity-derived IDs.
    """
    agent_id, tenant_id = _resolve_tenant_and_agent_id(turn_context)

    if msal_auth is not None:
        await _cache_observability_token(tenant_id, agent_id, msal_auth)

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


async def _cache_observability_token(tenant_id: str, agent_id: str, msal_auth: AccessTokenProviderBase) -> None:
    """Fetch and cache the observability token using activity-derived IDs.

    Equivalent to ``agentTokenCache.RegisterObservability()`` in C#.
    MSAL caches tokens internally, so repeated calls within the token lifetime
    do not incur additional network requests.
    """
    try:
        from microsoft_agents_a365.observability.core.config import get_observability_authentication_scope
    except ImportError:
        return

    try:
        token = await msal_auth.get_agentic_application_token(
            tenant_id, agent_id)
        cache_agentic_token(tenant_id, agent_id, token)
        logger.debug("Observability token cached (tenant=%s, agent=%s)", tenant_id, agent_id)
    except Exception as exc:
        logger.warning("Failed to cache observability token: %s", exc)


def _resolve_tenant_and_agent_id(turn_context) -> tuple[str, str]:
    """Extract tenant and agent IDs from the turn activity.

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
