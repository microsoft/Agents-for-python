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

    def display(self, start_time: float, end_time: float):
        """Display aggregated results."""
        print()
        print("---- Aggregated Results ----")
        print()
        print(f"Average Time: {self.average:.4f} seconds")
        print(f"Min Time:     {self.min:.4f} seconds")
        print(f"Max Time:     {self.max:.4f} seconds")
        print()
        print(f"Success Rate: {self.success_count} / {len(self._results)}")
        print()
        print(f"Total Time:   {end_time - start_time} seconds")
        print("----------------------------")
        print()

    def display_timeline(self):
        """Display timeline of individual execution results."""
        print()
        print("---- Execution Timeline ----")
        print(
            "Each '.' represents 1 second of successful execution. So a line like '...' is a success that took 3 seconds (rounded up), 'x' represents a failure."
        )
        print()
        for result in sorted(self._results, key=lambda r: r.exe_id):
            c = "." if result.success else "x"
            if c == ".":
                duration = int(round(result.duration))
                for _ in range(1 + duration):
                    print(c, end="")
                print()
            else:
                print(c)

        print("----------------------------")
        print()
