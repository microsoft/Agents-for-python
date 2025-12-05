from microsoft_agents.testing.cli.common import ExecutionResult

def output_results(results: list[ExecutionResult]) -> None:
    """Output the results of the benchmark to the console."""

    for result in results:
        status = "Success" if result.success else "Failure"
        print(
            f"Execution ID: {result.exe_id}, Duration: {result.duration:.4f} seconds, Status: {status}"
        )
        print(result.result)
