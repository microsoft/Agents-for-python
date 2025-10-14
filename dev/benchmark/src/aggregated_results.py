from .executor import ExecutionResult

class AggregatedResults:
    """Class to analyze execution time results."""

    def __init__(self, results: list[ExecutionResult]):
        self._results = results

        self.average = sum(r.duration for r in results) / len(results) if results else 0
        self.min = min((r.duration for r in results), default=0)
        self.max = max((r.duration for r in results), default=0)
        self.success_count = sum(1 for r in results if r.success)
        self.failure_count = len(results) - self.success_count
        self.total_time = sum(r.duration for r in results)