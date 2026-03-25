from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.authorization.telemetry.spans import (
    GetAccessToken,
    AcquireTokenOnBehalfOf,
    GetAgenticInstanceToken,
    GetAgenticUserToken,
)
from microsoft_agents.hosting.core.authorization.telemetry import constants

from tests._common.fixtures.telemetry import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


# ---- GetAccessToken ----


def test_get_access_token_creates_span(test_exporter):
    with GetAccessToken(["User.Read"], "client_credentials"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_GET_ACCESS_TOKEN


def test_get_access_token_span_attributes(test_exporter):
    with GetAccessToken(["User.Read", "Mail.Read"], "client_credentials"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_SCOPES] == "User.Read,Mail.Read"
    assert span.attributes[attributes.AUTH_METHOD] == "client_credentials"


def test_get_access_token_records_metrics(test_exporter, test_metric_reader):
    with GetAccessToken(["scope"], "client_credentials"):
        pass

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(find_metric(data, constants.METRIC_AUTH_TOKEN_REQUEST_COUNT))
    assert count == 1
    duration = sum_hist_count(
        find_metric(data, constants.METRIC_AUTH_TOKEN_REQUEST_DURATION)
    )
    assert duration == 1


# ---- AcquireTokenOnBehalfOf ----


def test_acquire_token_obo_creates_span(test_exporter):
    with AcquireTokenOnBehalfOf(["User.Read"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_ACQUIRE_TOKEN_ON_BEHALF_OF


def test_acquire_token_obo_span_attributes(test_exporter):
    with AcquireTokenOnBehalfOf(["User.Read"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_SCOPES] == "User.Read"


def test_acquire_token_obo_records_metrics(test_exporter, test_metric_reader):
    with AcquireTokenOnBehalfOf(["scope"]):
        pass

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_AUTH_TOKEN_REQUEST_COUNT),
        {attributes.AUTH_METHOD: constants.AUTH_METHOD_OBO},
    )
    assert count == 1


# ---- GetAgenticInstanceToken ----


def test_get_agentic_instance_token_creates_span(test_exporter):
    with GetAgenticInstanceToken("instance-42"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_GET_AGENTIC_INSTANCE_TOKEN


def test_get_agentic_instance_token_span_attributes(test_exporter):
    with GetAgenticInstanceToken("instance-42"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AGENTIC_INSTANCE_ID] == "instance-42"


def test_get_agentic_instance_token_records_metrics(test_exporter, test_metric_reader):
    with GetAgenticInstanceToken("instance-42"):
        pass

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_AUTH_TOKEN_REQUEST_COUNT),
        {attributes.AUTH_METHOD: constants.AUTH_METHOD_AGENTIC_INSTANCE},
    )
    assert count == 1


# ---- GetAgenticUserToken ----


def test_get_agentic_user_token_creates_span(test_exporter):
    with GetAgenticUserToken("instance-1", "user-1", ["scope"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_GET_AGENTIC_USER_TOKEN


def test_get_agentic_user_token_span_attributes(test_exporter):
    with GetAgenticUserToken("instance-1", "user-1", ["Scope.A", "Scope.B"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AGENTIC_INSTANCE_ID] == "instance-1"
    assert span.attributes[attributes.AGENTIC_USER_ID] == "user-1"
    assert span.attributes[attributes.AUTH_SCOPES] == "Scope.A,Scope.B"


def test_get_agentic_user_token_records_metrics(test_exporter, test_metric_reader):
    with GetAgenticUserToken("instance-1", "user-1", ["scope"]):
        pass

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_AUTH_TOKEN_REQUEST_COUNT),
        {attributes.AUTH_METHOD: constants.AUTH_METHOD_AGENTIC_USER},
    )
    assert count == 1
