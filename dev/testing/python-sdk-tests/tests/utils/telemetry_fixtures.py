import pytest
from types import SimpleNamespace

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


class DeltaMetricReader:
    """Wraps an InMemoryMetricReader so each test only sees metrics
    accrued *after* the wrapper was created (or last reset).

    InMemoryMetricReader uses cumulative aggregation by default and has
    no ``clear()`` method, so counters and histograms accumulate across
    the whole session.  This wrapper snapshots the cumulative values at
    construction time and subtracts them from every subsequent
    ``get_metrics_data()`` call, producing a delta view that is
    compatible with the ``find_metric`` / ``sum_counter`` /
    ``sum_hist_count`` helpers.
    """

    def __init__(self, inner: InMemoryMetricReader):
        self._inner = inner
        self._baseline: dict[tuple, tuple] = {}
        self.reset()

    def reset(self):
        """Capture the current cumulative values as the new zero-line."""
        data = self._inner.get_metrics_data()
        self._baseline = self._snapshot(data)

    def force_flush(self):
        self._inner.force_flush()

    def get_metrics_data(self):
        """Return a metrics-data object containing only the delta
        since the last ``reset()``."""
        raw = self._inner.get_metrics_data()
        return self._subtract(raw, self._baseline)

    # -- internals --------------------------------------------------

    @staticmethod
    def _dp_key(metric_name, dp):
        attrs = dp.attributes or {}
        return (metric_name, tuple(sorted(attrs.items())))

    @staticmethod
    def _snapshot(data):
        snap: dict[tuple, tuple] = {}
        if data is None:
            return snap
        for rm in data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    for dp in m.data.data_points:
                        k = DeltaMetricReader._dp_key(m.name, dp)
                        if hasattr(dp, "bucket_counts"):
                            snap[k] = ("hist", dp.count)
                        else:
                            snap[k] = ("counter", dp.value)
        return snap

    @staticmethod
    def _empty_data():
        return SimpleNamespace(
            resource_metrics=[
                SimpleNamespace(scope_metrics=[SimpleNamespace(metrics=[])])
            ]
        )

    @staticmethod
    def _subtract(data, baseline):
        if data is None:
            return DeltaMetricReader._empty_data()
        all_metrics: list = []
        for rm in data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    points: list = []
                    for dp in m.data.data_points:
                        k = DeltaMetricReader._dp_key(m.name, dp)
                        base = baseline.get(k)
                        if hasattr(dp, "bucket_counts"):
                            base_count = base[1] if base else 0
                            points.append(
                                SimpleNamespace(
                                    attributes=dp.attributes,
                                    count=dp.count - base_count,
                                )
                            )
                        else:
                            base_val = base[1] if base else 0
                            points.append(
                                SimpleNamespace(
                                    attributes=dp.attributes,
                                    value=dp.value - base_val,
                                )
                            )
                    if points:
                        all_metrics.append(
                            SimpleNamespace(
                                name=m.name,
                                data=SimpleNamespace(data_points=points),
                            )
                        )
        return SimpleNamespace(
            resource_metrics=[
                SimpleNamespace(scope_metrics=[SimpleNamespace(metrics=all_metrics)])
            ]
        )


_metric_reader = None
_exporter = None


@pytest.fixture(scope="session")
def test_telemetry():
    """Set up fresh in-memory exporter for testing."""
    global _exporter, _metric_reader

    if _exporter is None:
        exporter = InMemorySpanExporter()
        metric_reader = InMemoryMetricReader()

        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(tracer_provider)

        meter_provider = MeterProvider([metric_reader])

        metrics.set_meter_provider(meter_provider)

        _exporter = exporter
        _metric_reader = metric_reader
    else:
        meter_provider = metrics.get_meter_provider()
        tracer_provider = trace.get_tracer_provider()

        exporter = _exporter
        metric_reader = _metric_reader

    yield _exporter, metric_reader

    exporter.clear()


@pytest.fixture(scope="function")
def test_exporter(test_telemetry):
    """Provide the in-memory span exporter for each test."""
    exporter, _ = test_telemetry
    exporter.clear()
    return exporter


@pytest.fixture(scope="function")
def test_metric_reader(test_telemetry):
    """Provide a delta view of the metric reader for each test.
    Only metrics recorded *during* the test are visible."""
    _, metric_reader = test_telemetry
    metric_reader.force_flush()
    return DeltaMetricReader(metric_reader)
