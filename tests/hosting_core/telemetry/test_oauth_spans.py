from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.app.oauth.telemetry.spans import (
    AgenticToken,
    AzureBotToken,
    AzureBotSignIn,
    AzureBotSignOut,
)
from microsoft_agents.hosting.core.app.oauth.telemetry import constants

from tests._common.fixtures.telemetry import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)

# ---- AgenticToken ----


def test_agentic_token_creates_span(test_exporter):
    with AgenticToken("handler-1", "conn-1", ["scope"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AGENTIC_TOKEN


def test_agentic_token_span_attributes(test_exporter):
    with AgenticToken("handler-1", "conn-1", ["Scope.A", "Scope.B"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_HANDLER_ID] == "handler-1"
    assert span.attributes[attributes.CONNECTION_NAME] == "conn-1"
    assert span.attributes[attributes.AUTH_SCOPES] == "Scope.A,Scope.B"


def test_agentic_token_no_connection(test_exporter):
    with AgenticToken("handler-1", None, ["scope"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.CONNECTION_NAME] == attributes.UNKNOWN


def test_agentic_token_no_scopes(test_exporter):
    with AgenticToken("handler-1", "conn-1", None):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert attributes.AUTH_SCOPES not in span.attributes


# ---- AzureBotToken ----


def test_azure_bot_token_creates_span(test_exporter):
    with AzureBotToken("handler-2", "conn-2", ["scope"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AZURE_BOT_TOKEN


def test_azure_bot_token_span_attributes(test_exporter):
    with AzureBotToken("handler-2", "conn-2", ["Mail.Read"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_HANDLER_ID] == "handler-2"
    assert span.attributes[attributes.CONNECTION_NAME] == "conn-2"
    assert span.attributes[attributes.AUTH_SCOPES] == "Mail.Read"


# ---- AzureBotSignIn ----


def test_azure_bot_sign_in_creates_span(test_exporter):
    with AzureBotSignIn("handler-3", "conn-3", ["scope"]):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AZURE_BOT_SIGN_IN


def test_azure_bot_sign_in_span_attributes(test_exporter):
    with AzureBotSignIn("handler-3", "conn-3", ["User.Read"]):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_HANDLER_ID] == "handler-3"
    assert span.attributes[attributes.CONNECTION_NAME] == "conn-3"
    assert span.attributes[attributes.AUTH_SCOPES] == "User.Read"


# ---- AzureBotSignOut ----


def test_azure_bot_sign_out_creates_span(test_exporter):
    with AzureBotSignOut("handler-4"):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.AZURE_BOT_SIGN_OUT


def test_azure_bot_sign_out_span_attributes(test_exporter):
    with AzureBotSignOut("handler-4"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.AUTH_HANDLER_ID] == "handler-4"
    assert span.attributes[attributes.CONNECTION_NAME] == attributes.UNKNOWN


def test_azure_bot_sign_out_no_scopes_in_attributes(test_exporter):
    with AzureBotSignOut("handler-4"):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert attributes.AUTH_SCOPES not in span.attributes
