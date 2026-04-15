# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from opentelemetry import trace

from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.connector.telemetry.user_token_client_spans import (
    GetUserToken,
    SignOut,
    GetSignInResource,
    ExchangeToken,
    GetTokenOrSignInResource,
    GetTokenStatus,
    GetAadTokens,
)
from microsoft_agents.hosting.core.connector.telemetry import constants

from tests._common.fixtures.telemetry import (  # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


# ---- GetUserToken ----


def test_get_user_token_creates_span(test_exporter):
    with GetUserToken("conn-1", "user-1", "msteams"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_USER_TOKEN


def test_get_user_token_span_attributes(test_exporter):
    with GetUserToken("my-connection", "user-abc", "webchat"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == "my-connection"
    assert span.attributes[attributes.USER_ID] == "user-abc"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "webchat"


def test_get_user_token_no_channel_defaults_to_unknown(test_exporter):
    with GetUserToken("conn-1", "user-1"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].attributes[attributes.ACTIVITY_CHANNEL_ID]
        == attributes.UNKNOWN
    )


def test_get_user_token_records_metrics(test_exporter, test_metric_reader):
    with GetUserToken("conn-1", "user-1", "msteams") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )
    assert (
        sum_hist_count(
            find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_DURATION)
        )
        == 1
    )


# ---- SignOut ----


def test_sign_out_creates_span(test_exporter):
    with SignOut("conn-1", "user-1", "msteams"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_SIGN_OUT


def test_sign_out_span_attributes(test_exporter):
    with SignOut("conn-logout", "user-2", "directline"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == "conn-logout"
    assert span.attributes[attributes.USER_ID] == "user-2"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "directline"


def test_sign_out_none_connection_name_defaults_to_unknown(test_exporter):
    with SignOut(None, "user-2"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].attributes[attributes.CONNECTION_NAME]
        == attributes.UNKNOWN
    )


def test_sign_out_records_metrics(test_exporter, test_metric_reader):
    with SignOut("conn-1", "user-1") as span:
        span.share(http_method="DELETE", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- GetSignInResource ----


def test_get_sign_in_resource_creates_span(test_exporter):
    with GetSignInResource():
        pass

    assert (
        test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_SIGN_IN_RESOURCE
    )


def test_get_sign_in_resource_all_attributes_are_unknown(test_exporter):
    """GetSignInResource accepts no parameters, so all attributes default to UNKNOWN.
    NOTE: this is a known gap — connection_name should be required per the spec."""
    with GetSignInResource():
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == attributes.UNKNOWN
    assert span.attributes[attributes.USER_ID] == attributes.UNKNOWN
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == attributes.UNKNOWN


def test_get_sign_in_resource_records_metrics(test_exporter, test_metric_reader):
    with GetSignInResource() as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- ExchangeToken ----


def test_exchange_token_creates_span(test_exporter):
    with ExchangeToken("conn-1", "user-1", "msteams"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_EXCHANGE_TOKEN


def test_exchange_token_span_attributes(test_exporter):
    with ExchangeToken("exchange-conn", "user-3", "msteams"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == "exchange-conn"
    assert span.attributes[attributes.USER_ID] == "user-3"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "msteams"


def test_exchange_token_records_metrics(test_exporter, test_metric_reader):
    with ExchangeToken("conn-1", "user-1") as span:
        span.share(http_method="POST", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- GetTokenOrSignInResource ----


def test_get_token_or_sign_in_resource_creates_span(test_exporter):
    with GetTokenOrSignInResource("conn-1", "user-1"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].name
        == constants.SPAN_GET_TOKEN_OR_SIGN_IN_RESOURCE
    )


def test_get_token_or_sign_in_resource_span_attributes(test_exporter):
    with GetTokenOrSignInResource("tosi-conn", "user-4", "webchat"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == "tosi-conn"
    assert span.attributes[attributes.USER_ID] == "user-4"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "webchat"


def test_get_token_or_sign_in_resource_records_metrics(test_exporter, test_metric_reader):
    with GetTokenOrSignInResource("conn-1", "user-1") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- GetTokenStatus ----


def test_get_token_status_creates_span(test_exporter):
    with GetTokenStatus("user-1", "msteams"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_TOKEN_STATUS


def test_get_token_status_span_attributes(test_exporter):
    with GetTokenStatus("user-5", "directline"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.USER_ID] == "user-5"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "directline"
    # GetTokenStatus takes no connection_name — defaults to UNKNOWN
    assert span.attributes[attributes.CONNECTION_NAME] == attributes.UNKNOWN


def test_get_token_status_records_metrics(test_exporter, test_metric_reader):
    with GetTokenStatus("user-1") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- GetAadTokens ----


def test_get_aad_tokens_creates_span(test_exporter):
    with GetAadTokens("conn-1", "user-1", "msteams"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_AAD_TOKENS


def test_get_aad_tokens_span_attributes(test_exporter):
    with GetAadTokens("aad-conn", "user-6", "msteams"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == "aad-conn"
    assert span.attributes[attributes.USER_ID] == "user-6"
    assert span.attributes[attributes.ACTIVITY_CHANNEL_ID] == "msteams"


def test_get_aad_tokens_records_metrics(test_exporter, test_metric_reader):
    with GetAadTokens("conn-1", "user-1") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert (
        sum_counter(find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT))
        == 1
    )


# ---- share() / _RequestSpanWrapper behavior ----


def test_share_http_attrs_go_to_metrics_not_span(test_exporter, test_metric_reader):
    """HTTP method and status code appear in metrics but not on the span itself."""
    with GetUserToken("conn-1", "user-1") as span:
        span.share(http_method="GET", status_code=200)

    finished = test_exporter.get_finished_spans()[0]
    # Not on the span
    assert attributes.HTTP_METHOD not in finished.attributes
    assert attributes.HTTP_STATUS_CODE not in finished.attributes

    # Present in metrics
    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_USER_TOKEN_CLIENT_REQUEST_COUNT),
        attribute_filter={
            attributes.HTTP_METHOD: "GET",
            attributes.HTTP_STATUS_CODE: 200,
        },
    )
    assert count == 1


def test_user_token_span_status_error_on_exception(test_exporter):
    with pytest.raises(ValueError):
        with GetUserToken("conn-1", "user-1"):
            raise ValueError("token error")

    assert (
        test_exporter.get_finished_spans()[0].status.status_code
        == trace.StatusCode.ERROR
    )
