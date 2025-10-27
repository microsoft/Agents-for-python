import logging
from unittest.mock import patch
from io import StringIO

from microsoft_agents.activity._utils import _DeferredString


class TestDeferredString:
    """Test suite for _DeferredString class."""

    def test_deferred_string_evaluation_basic(self):
        """Test basic string evaluation with function and args."""

        def sample_func(x, y):
            return f"Result is {x + y}"

        deferred = _DeferredString(sample_func, 2, 3)
        assert str(deferred) == "Result is 5"

    def test_deferred_string_evaluation_with_kwargs(self):
        """Test string evaluation with keyword arguments."""

        def sample_func(a, b=0, c=1):
            return f"Sum is {a + b + c}"

        deferred = _DeferredString(sample_func, 5, b=10, c=15)
        assert str(deferred) == "Sum is 30"

    def test_deferred_string_evaluation_mixed_args(self):
        """Test string evaluation with both positional and keyword arguments."""

        def sample_func(prefix, value, suffix="end"):
            return f"{prefix}-{value}-{suffix}"

        deferred = _DeferredString(sample_func, "start", 42, suffix="finish")
        assert str(deferred) == "start-42-finish"

    def test_deferred_string_no_args(self):
        """Test string evaluation with no arguments."""

        def simple_func():
            return "No args here"

        deferred = _DeferredString(simple_func)
        assert str(deferred) == "No args here"

    def test_deferred_string_complex_return_type(self):
        """Test that non-string return values are converted to strings."""

        def return_number():
            return 42

        deferred = _DeferredString(return_number)
        assert str(deferred) == "42"

    def test_deferred_string_none_return(self):
        """Test handling of None return value."""

        def return_none():
            return None

        deferred = _DeferredString(return_none)
        assert str(deferred) == "None"

    def test_deferred_string_exception_handling(self, caplog):
        """Test exception handling during function evaluation."""

        def faulty_func():
            raise ValueError("Intentional error")

        deferred = _DeferredString(faulty_func)

        with caplog.at_level(logging.ERROR):
            result = str(deferred)

        assert result == "_DeferredString: error evaluating deferred string"
        assert any(
            "Error evaluating deferred string" in message for message in caplog.messages
        )

    def test_deferred_string_exception_with_args(self, caplog):
        """Test exception handling when function is called with arguments."""

        def faulty_func(x, y):
            raise RuntimeError("Something went wrong")

        deferred = _DeferredString(faulty_func, 1, 2)

        with caplog.at_level(logging.ERROR):
            result = str(deferred)

        assert result == "_DeferredString: error evaluating deferred string"
        assert "Error evaluating deferred string" in caplog.text

    def test_deferred_string_logging_integration(self):
        """Test integration with logging module using deferred string in log messages."""
        # Create a string buffer to capture log output
        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.INFO)

        # Create a logger and add the handler
        test_logger = logging.getLogger("test_deferred_logger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(ch)

        def expensive_operation():
            return "Expensive computation result"

        deferred = _DeferredString(expensive_operation)

        # Log a message with the deferred string
        test_logger.info("Processing complete: %s", deferred)

        # Get the log output and verify the deferred string was evaluated
        log_contents = log_capture_string.getvalue()
        assert "Processing complete: Expensive computation result" in log_contents

        # Clean up
        test_logger.removeHandler(ch)

    def test_deferred_string_lazy_evaluation(self):
        """Test that the function is only called when string conversion occurs."""
        call_count = 0

        def counting_func():
            nonlocal call_count
            call_count += 1
            return f"Called {call_count} times"

        deferred = _DeferredString(counting_func)

        # Function should not be called yet
        assert call_count == 0

        # First string conversion should call the function
        result1 = str(deferred)
        assert call_count == 1
        assert result1 == "Called 1 times"

        # Second string conversion should call the function again
        result2 = str(deferred)
        assert call_count == 2
        assert result2 == "Called 2 times"

    def test_deferred_string_with_logger_level_filtering(self):
        """Test that deferred strings are only evaluated when log level allows it."""

        log_capture_string = StringIO()
        ch = logging.StreamHandler(log_capture_string)
        test_logger = logging.getLogger("multi_deferred_logger")
        test_logger.setLevel(logging.INFO)
        test_logger.addHandler(ch)

        def expensive_func():
            return "test"

        deferred = _DeferredString(expensive_func)

        # Log at DEBUG level - should not evaluate deferred string due to level filtering
        test_logger.debug("Debug message: %s", deferred)
        assert log_capture_string.getvalue() == ""

        # Log at ERROR level - should evaluate deferred string
        test_logger.error("Error message: %s", deferred)
        assert log_capture_string.getvalue() == "Error message: test\n"

        test_logger.removeHandler(ch)
