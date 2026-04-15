# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from opentelemetry import trace

from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.connector.telemetry.connector_spans import (
    ConnectorReplyToActivity,
    ConnectorSendToConversation,
    ConnectorUpdateActivity,
    ConnectorDeleteActivity,
    ConnectorCreateConversation,
    ConnectorGetConversations,
    ConnectorGetConversationMembers,
    ConnectorUploadAttachment,
    ConnectorGetAttachmentInfo,
    ConnectorGetAttachment,
)
from microsoft_agents.hosting.core.connector.telemetry import constants

from tests._common.fixtures.telemetry import (  # unused imports are needed for fixtures
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


# ---- ConnectorReplyToActivity ----


def test_connector_reply_to_activity_creates_span(test_exporter):
    with ConnectorReplyToActivity("conv-1", "act-1"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_REPLY_TO_ACTIVITY


def test_connector_reply_to_activity_span_attributes(test_exporter):
    with ConnectorReplyToActivity("conv-abc", "act-xyz"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-abc"
    assert span.attributes[attributes.ACTIVITY_ID] == "act-xyz"


def test_connector_reply_to_activity_records_metrics(test_exporter, test_metric_reader):
    with ConnectorReplyToActivity("conv-1", "act-1") as span:
        span.share(http_method="POST", status_code=200)

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT))
    assert count == 1
    duration = sum_hist_count(
        find_metric(data, constants.METRIC_CONNECTOR_REQUEST_DURATION)
    )
    assert duration == 1


def test_connector_reply_to_activity_metrics_include_http_attrs(
    test_exporter, test_metric_reader
):
    with ConnectorReplyToActivity("conv-1", "act-1") as span:
        span.share(http_method="POST", status_code=200)

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT),
        attribute_filter={
            attributes.HTTP_METHOD: "POST",
            attributes.HTTP_STATUS_CODE: 200,
        },
    )
    assert count == 1


def test_connector_span_without_share_omits_http_attrs_from_metrics(
    test_exporter, test_metric_reader
):
    """When share() is never called, http_method and status_code are absent from metrics."""
    with ConnectorReplyToActivity("conv-1", "act-1"):
        pass

    data = test_metric_reader.get_metrics_data()
    # Total count still recorded
    total = sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT))
    assert total == 1
    # But filtering by http_method finds nothing
    with_method = sum_counter(
        find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT),
        attribute_filter={attributes.HTTP_METHOD: "POST"},
    )
    assert with_method == 0


def test_connector_span_operation_attribute_is_span_name(
    test_exporter, test_metric_reader
):
    """Metrics include OPERATION set to the span name."""
    with ConnectorReplyToActivity("conv-1", "act-1") as span:
        span.share(http_method="POST", status_code=200)

    data = test_metric_reader.get_metrics_data()
    count = sum_counter(
        find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT),
        attribute_filter={attributes.OPERATION: constants.SPAN_REPLY_TO_ACTIVITY},
    )
    assert count == 1


def test_connector_span_status_ok_on_success(test_exporter):
    with ConnectorReplyToActivity("conv-1", "act-1"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].status.status_code
        == trace.StatusCode.OK
    )


def test_connector_span_status_error_on_exception(test_exporter):
    with pytest.raises(RuntimeError):
        with ConnectorReplyToActivity("conv-1", "act-1"):
            raise RuntimeError("connector failure")

    assert (
        test_exporter.get_finished_spans()[0].status.status_code
        == trace.StatusCode.ERROR
    )


# ---- ConnectorSendToConversation ----


def test_connector_send_to_conversation_creates_span(test_exporter):
    with ConnectorSendToConversation("conv-1", "act-1"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_SEND_TO_CONVERSATION


def test_connector_send_to_conversation_span_attributes(test_exporter):
    with ConnectorSendToConversation("conv-2", None):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-2"
    assert attributes.ACTIVITY_ID not in span.attributes


def test_connector_send_to_conversation_records_metrics(test_exporter, test_metric_reader):
    with ConnectorSendToConversation("conv-1", None) as span:
        span.share(http_method="POST", status_code=201)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorUpdateActivity ----


def test_connector_update_activity_creates_span(test_exporter):
    with ConnectorUpdateActivity("conv-1", "act-1"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_UPDATE_ACTIVITY


def test_connector_update_activity_span_attributes(test_exporter):
    with ConnectorUpdateActivity("conv-3", "act-3"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-3"
    assert span.attributes[attributes.ACTIVITY_ID] == "act-3"


def test_connector_update_activity_records_metrics(test_exporter, test_metric_reader):
    with ConnectorUpdateActivity("conv-1", "act-1") as span:
        span.share(http_method="PUT", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorDeleteActivity ----


def test_connector_delete_activity_creates_span(test_exporter):
    with ConnectorDeleteActivity("conv-1", "act-1"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_DELETE_ACTIVITY


def test_connector_delete_activity_span_attributes(test_exporter):
    with ConnectorDeleteActivity("conv-4", "act-4"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONVERSATION_ID] == "conv-4"
    assert span.attributes[attributes.ACTIVITY_ID] == "act-4"


def test_connector_delete_activity_records_metrics(test_exporter, test_metric_reader):
    with ConnectorDeleteActivity("conv-1", "act-1") as span:
        span.share(http_method="DELETE", status_code=204)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorCreateConversation ----


def test_connector_create_conversation_creates_span(test_exporter):
    with ConnectorCreateConversation():
        pass

    assert (
        test_exporter.get_finished_spans()[0].name == constants.SPAN_CREATE_CONVERSATION
    )


def test_connector_create_conversation_has_no_conversation_or_activity_attrs(
    test_exporter,
):
    with ConnectorCreateConversation():
        pass

    span = test_exporter.get_finished_spans()[0]
    assert attributes.CONVERSATION_ID not in span.attributes
    assert attributes.ACTIVITY_ID not in span.attributes


def test_connector_create_conversation_records_metrics(test_exporter, test_metric_reader):
    with ConnectorCreateConversation() as span:
        span.share(http_method="POST", status_code=201)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorGetConversations ----


def test_connector_get_conversations_creates_span(test_exporter):
    with ConnectorGetConversations():
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_CONVERSATIONS


def test_connector_get_conversations_records_metrics(test_exporter, test_metric_reader):
    with ConnectorGetConversations() as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorGetConversationMembers ----


def test_connector_get_conversation_members_creates_span(test_exporter):
    with ConnectorGetConversationMembers():
        pass

    assert (
        test_exporter.get_finished_spans()[0].name
        == constants.SPAN_GET_CONVERSATION_MEMBERS
    )


def test_connector_get_conversation_members_records_metrics(
    test_exporter, test_metric_reader
):
    with ConnectorGetConversationMembers() as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorUploadAttachment ----


def test_connector_upload_attachment_creates_span(test_exporter):
    with ConnectorUploadAttachment("conv-5"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].name == constants.SPAN_UPLOAD_ATTACHMENT
    )


def test_connector_upload_attachment_span_attributes(test_exporter):
    with ConnectorUploadAttachment("conv-5"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].attributes[attributes.CONVERSATION_ID]
        == "conv-5"
    )


def test_connector_upload_attachment_records_metrics(test_exporter, test_metric_reader):
    with ConnectorUploadAttachment("conv-5") as span:
        span.share(http_method="POST", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorGetAttachmentInfo ----


def test_connector_get_attachment_info_creates_span(test_exporter):
    with ConnectorGetAttachmentInfo("attach-1"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_ATTACHMENT_INFO
    )


def test_connector_get_attachment_info_span_attributes(test_exporter):
    with ConnectorGetAttachmentInfo("attach-abc"):
        pass

    assert (
        test_exporter.get_finished_spans()[0].attributes[attributes.ATTACHMENT_ID]
        == "attach-abc"
    )


def test_connector_get_attachment_info_records_metrics(test_exporter, test_metric_reader):
    with ConnectorGetAttachmentInfo("attach-1") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1


# ---- ConnectorGetAttachment ----


def test_connector_get_attachment_creates_span(test_exporter):
    with ConnectorGetAttachment("attach-1", "original"):
        pass

    assert test_exporter.get_finished_spans()[0].name == constants.SPAN_GET_ATTACHMENT


def test_connector_get_attachment_span_attributes(test_exporter):
    with ConnectorGetAttachment("attach-xyz", "thumbnail"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.ATTACHMENT_ID] == "attach-xyz"
    assert span.attributes[attributes.VIEW_ID] == "thumbnail"


def test_connector_get_attachment_records_metrics(test_exporter, test_metric_reader):
    with ConnectorGetAttachment("attach-1", "original") as span:
        span.share(http_method="GET", status_code=200)

    data = test_metric_reader.get_metrics_data()
    assert sum_counter(find_metric(data, constants.METRIC_CONNECTOR_REQUEST_COUNT)) == 1
