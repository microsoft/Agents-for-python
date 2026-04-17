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
import jwt  # PyJWT library
from typing import Awaitable, Callable, Optional

from microsoft_agents.hosting.core import Authorization, TurnContext
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
    turn_context: TurnContext,
    turn_state,
    func: Callable[[], Awaitable[None]],
    user_authorization: Optional[Authorization] = None,
    auth_handler: Optional[str] = None,
) -> None:
    """Wrap an agent operation with A365 observability baggage context.

    Equivalent to ``A365OtelWrapper.InvokeObservedAgentOperation()`` in C#.

    Resolves the tenant ID and agent ID from the activity, sets them as
    OpenTelemetry baggage (equivalent to the C# ``BaggageBuilder``), caches
    the observability token per-turn when ``user_authorization`` is provided (equivalent
    to ``agentTokenCache.RegisterObservability()``), then delegates to
    :func:`~telemetry.agent_metrics.invoke_observed_agent_operation` for span
    management and metric recording.

    Args:
        operation_name: Human-readable name of the operation / handler.
        turn_context: The current :class:`TurnContext`.
        turn_state: The current :class:`TurnState`.
        func: Async function containing the agent logic to execute.
        user_authorization: Optional MSAL authentication provider used to fetch and
            cache the observability token for the activity-derived IDs.
    """
    agent_id, tenant_id = await _resolve_tenant_and_agent_id(turn_context, user_authorization, auth_handler)

    if user_authorization is not None:
        await _cache_observability_token(tenant_id, agent_id, user_authorization)

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


async def _cache_observability_token(tenant_id: str, agent_id: str, authorization: Authorization) -> None:
    """Fetch and cache the observability token using activity-derived IDs.

    Equivalent to ``agentTokenCache.RegisterObservability()`` in C#.
    MSAL caches tokens internally, so repeated calls within the token lifetime
    do not incur additional network requests.
    """

    try:
        token = await authorization.get_token(tenant_id, agent_id)
        cache_agentic_token(tenant_id, agent_id, token)
        logger.debug("Observability token cached (tenant=%s, agent=%s)", tenant_id, agent_id)
    except Exception as exc:
        logger.warning("Failed to cache observability token: %s", exc)


async def _resolve_tenant_and_agent_id(turn_context: TurnContext, user_authorization: Optional[Authorization] = None, auth_handler: Optional[str] = None) -> tuple[str, str]:
    """Extract tenant and agent IDs from the turn activity.

    Args:
        turn_context: The current :class:`TurnContext`.
        user_authorization: Optional MSAL authentication provider used to fetch the token.
        auth_handler: Optional string representing the authentication handler.

    Returns:
        ``(agent_id, tenant_id)`` as strings.
    """
    activity = turn_context.activity
    if activity is None:
        return _EMPTY_GUID, _EMPTY_GUID
    
    agentic_token = await user_authorization.get_token(turn_context, auth_handler or "AGENTIC") if user_authorization else None
    

    agent_id = activity.get_agentic_instance_id() if activity.is_agentic_request() else _get_app_id_from_token(agentic_token)
    agent_id = agent_id or _EMPTY_GUID
    
    tenant_id = activity.conversation.tenant_id if activity.conversation and activity.conversation.tenant_id else _EMPTY_GUID

    return agent_id, tenant_id

def _get_app_id_from_token(token: str) -> str:
    """Extract the app ID from the JWT token."""
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        app_id = decoded.get("appid") or decoded.get("azp") or _EMPTY_GUID
        return str(app_id)
    except Exception as exc:
        logger.warning("Failed to decode token for app ID extraction: %s", exc)
        return _EMPTY_GUID
