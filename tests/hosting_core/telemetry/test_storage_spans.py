from microsoft_agents.hosting.core.telemetry import attributes
from microsoft_agents.hosting.core.storage.telemetry.spans import (
    StorageRead,
    StorageWrite,
    StorageDelete,
)
from microsoft_agents.hosting.core.storage.telemetry import constants

from tests._common.fixtures.telemetry import (
    test_telemetry,
    test_exporter,
    test_metric_reader,
)
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count

# ---- StorageRead ----


def test_storage_read_creates_span(test_exporter):
    with StorageRead(key_count=3):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_STORAGE_READ


def test_storage_read_span_attributes(test_exporter):
    with StorageRead(key_count=5):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.KEY_COUNT] == 5


def test_storage_read_records_metrics(test_exporter, test_metric_reader):
    with StorageRead(key_count=1):
        pass

    data = test_metric_reader.get_metrics_data()
    total = sum_counter(find_metric(data, constants.METRIC_STORAGE_OPERATION_TOTAL))
    assert total == 1
    duration = sum_hist_count(
        find_metric(data, constants.METRIC_STORAGE_OPERATION_DURATION)
    )
    assert duration == 1


# ---- StorageWrite ----


def test_storage_write_creates_span(test_exporter):
    with StorageWrite(key_count=2):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_STORAGE_WRITE


def test_storage_write_span_attributes(test_exporter):
    with StorageWrite(key_count=7):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.KEY_COUNT] == 7


def test_storage_write_records_metrics(test_exporter, test_metric_reader):
    with StorageWrite(key_count=1):
        pass

    data = test_metric_reader.get_metrics_data()
    total = sum_counter(find_metric(data, constants.METRIC_STORAGE_OPERATION_TOTAL))
    assert total == 1


# ---- StorageDelete ----


def test_storage_delete_creates_span(test_exporter):
    with StorageDelete(key_count=1):
        pass

    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == constants.SPAN_STORAGE_DELETE


def test_storage_delete_span_attributes(test_exporter):
    with StorageDelete(key_count=4):
        pass

    span = test_exporter.get_finished_spans()[0]
    assert span.attributes[attributes.KEY_COUNT] == 4


def test_storage_delete_records_metrics(test_exporter, test_metric_reader):
    with StorageDelete(key_count=1):
        pass

    data = test_metric_reader.get_metrics_data()
    total = sum_counter(find_metric(data, constants.METRIC_STORAGE_OPERATION_TOTAL))
    assert total == 1
