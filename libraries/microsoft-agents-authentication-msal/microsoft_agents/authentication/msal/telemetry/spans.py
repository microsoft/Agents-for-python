from contextlib import contextmanager
from collections.abc import Iterator

from microsoft_agents.hosting.core.telemetry import (
    agents_telemetry,
    constants as common_constants,
    _format_scopes
)

from . import constants, _metrics

@contextmanager
def start_span_auth_get_access_token(scopes: list[str], auth_type: str) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_ACCESS_TOKEN) as span:
        span.set_attributes({
            common_constants.ATTR_AUTH_SCOPES: _format_scopes(scopes),
            common_constants.ATTR_AUTH_TYPE: auth_type,
        })
        yield


@contextmanager
def start_span_auth_acquire_token_on_behalf_of(scopes: list[str]) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_ACQUIRE_TOKEN_ON_BEHALF_OF) as span:
        span.set_attribute(common_constants.ATTR_AUTH_SCOPES, _format_scopes(scopes))
        yield


@contextmanager
def start_span_auth_get_agentic_instance_token(agentic_instance_id: str) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_AGENTIC_INSTANCE_TOKEN) as span:
        span.set_attribute(common_constants.ATTR_AGENTIC_INSTANCE_ID, agentic_instance_id)
        yield


@contextmanager
def start_span_auth_get_agentic_user_token(agentic_instance_id: str, agentic_user_id: str, scopes: list[str]) -> Iterator[None]:
    with agents_telemetry.start_as_current_span(constants.SPAN_AUTH_GET_AGENTIC_USER_TOKEN):
        span.set_attributes({
            common_constants.ATTR_AGENTIC_INSTANCE_ID: agentic_instance_id,
            common_constants.ATTR_AGENTIC_USER_ID: agentic_user_id,
            common_constants.ATTR_AUTH_SCOPES: scopes,
        })
        yield