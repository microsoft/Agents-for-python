def _find_metric(metrics_data, metric_name):
    for resource_metric in metrics_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == metric_name:
                    return metric
    return None


def _sum_counter(metric, attribute_filter=None):
    if metric is None:
        return 0
    total = 0
    for point in metric.data.data_points:
        if attribute_filter is None or all(
            point.attributes.get(key) == value
            for key, value in attribute_filter.items()
        ):
            total += point.value
    return total


def _sum_hist_count(metric, attribute_filter=None):
    if metric is None:
        return 0
    total = 0
    for point in metric.data.data_points:
        if attribute_filter is None or all(
            point.attributes.get(key) == value
            for key, value in attribute_filter.items()
        ):
            total += point.count
    return total