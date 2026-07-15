from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from tests._common.fixtures.telemetry import DeltaMetricReader
from tests._common.telemetry_utils import find_metric, sum_counter, sum_hist_count


def _make_reader():
    """Create a standalone MeterProvider + InMemoryMetricReader pair."""
    inner = InMemoryMetricReader()
    provider = MeterProvider([inner])
    meter = provider.get_meter("test")
    return inner, provider, meter


# ---- basic counter delta ----


def test_counter_delta_excludes_baseline():
    inner, provider, meter = _make_reader()
    counter = meter.create_counter("my_counter")

    counter.add(5)
    delta = DeltaMetricReader(inner)  # baseline captures 5

    counter.add(3)
    data = delta.get_metrics_data()

    assert sum_counter(find_metric(data, "my_counter")) == 3
    provider.shutdown()


def test_counter_delta_is_zero_when_nothing_new():
    inner, provider, meter = _make_reader()
    counter = meter.create_counter("my_counter")

    counter.add(10)
    delta = DeltaMetricReader(inner)

    data = delta.get_metrics_data()
    metric = find_metric(data, "my_counter")
    # No new increments → metric either absent or zero
    assert metric is None or sum_counter(metric) == 0
    provider.shutdown()


def test_counter_accumulates_across_calls():
    inner, provider, meter = _make_reader()
    counter = meter.create_counter("my_counter")

    delta = DeltaMetricReader(inner)

    counter.add(2)
    counter.add(3)

    data = delta.get_metrics_data()
    assert sum_counter(find_metric(data, "my_counter")) == 5
    provider.shutdown()


# ---- reset ----


def test_reset_clears_delta():
    inner, provider, meter = _make_reader()
    counter = meter.create_counter("my_counter")

    delta = DeltaMetricReader(inner)
    counter.add(7)

    delta.reset()  # new baseline includes the 7

    data = delta.get_metrics_data()
    metric = find_metric(data, "my_counter")
    assert metric is None or sum_counter(metric) == 0

    counter.add(2)
    data = delta.get_metrics_data()
    assert sum_counter(find_metric(data, "my_counter")) == 2
    provider.shutdown()


# ---- histogram delta ----


def test_histogram_delta_excludes_baseline():
    inner, provider, meter = _make_reader()
    hist = meter.create_histogram("my_hist")

    hist.record(100)
    hist.record(200)
    delta = DeltaMetricReader(inner)  # baseline count=2

    hist.record(50)
    data = delta.get_metrics_data()

    assert sum_hist_count(find_metric(data, "my_hist")) == 1
    provider.shutdown()


def test_histogram_delta_is_zero_when_nothing_new():
    inner, provider, meter = _make_reader()
    hist = meter.create_histogram("my_hist")

    hist.record(42)
    delta = DeltaMetricReader(inner)

    data = delta.get_metrics_data()
    metric = find_metric(data, "my_hist")
    assert metric is None or sum_hist_count(metric) == 0
    provider.shutdown()


# ---- attribute-keyed counters ----


def test_counter_delta_respects_attributes():
    inner, provider, meter = _make_reader()
    counter = meter.create_counter("tagged")

    counter.add(10, attributes={"ch": "teams"})
    counter.add(20, attributes={"ch": "webchat"})

    delta = DeltaMetricReader(inner)

    counter.add(1, attributes={"ch": "teams"})
    counter.add(2, attributes={"ch": "webchat"})

    data = delta.get_metrics_data()
    metric = find_metric(data, "tagged")

    assert sum_counter(metric, {"ch": "teams"}) == 1
    assert sum_counter(metric, {"ch": "webchat"}) == 2
    provider.shutdown()


# ---- multiple metrics ----


def test_multiple_metrics_tracked_independently():
    inner, provider, meter = _make_reader()
    c1 = meter.create_counter("counter_a")
    c2 = meter.create_counter("counter_b")

    c1.add(100)
    delta = DeltaMetricReader(inner)

    c1.add(1)
    c2.add(5)

    data = delta.get_metrics_data()
    assert sum_counter(find_metric(data, "counter_a")) == 1
    assert sum_counter(find_metric(data, "counter_b")) == 5
    provider.shutdown()


# ---- new metric after baseline ----


def test_new_metric_after_baseline():
    inner, provider, meter = _make_reader()

    delta = DeltaMetricReader(inner)

    counter = meter.create_counter("late_counter")
    counter.add(3)

    data = delta.get_metrics_data()
    assert sum_counter(find_metric(data, "late_counter")) == 3
    provider.shutdown()


# ---- force_flush delegates ----


def test_force_flush_delegates():
    inner, provider, meter = _make_reader()
    delta = DeltaMetricReader(inner)

    counter = meter.create_counter("flushed")
    counter.add(1)
    delta.force_flush()

    data = delta.get_metrics_data()
    assert sum_counter(find_metric(data, "flushed")) == 1
    provider.shutdown()


# ---- output structure is compatible with find_metric ----


def test_output_structure_compatible_with_helpers():
    inner, provider, meter = _make_reader()
    delta = DeltaMetricReader(inner)

    counter = meter.create_counter("compat")
    counter.add(1)

    data = delta.get_metrics_data()

    # Test that the structure is compatible with find_metric helper
    m = find_metric(data, "compat")
    assert m is not None
    assert m.name == "compat"
    assert hasattr(m.data, "data_points")
    dp = m.data.data_points[0]
    assert hasattr(dp, "value")
    assert hasattr(dp, "attributes")
    provider.shutdown()
