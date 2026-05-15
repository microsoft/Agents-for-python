"""DateTime helper tools."""
from datetime import datetime
from typing import Annotated
from pydantic import Field


def get_date_time(
    input_text: Annotated[str, Field(description="User input (not used, can be empty)")] = ""
) -> str:
    """
    Get the current date and time.

    Args:
        input_text: Optional user input (not used by this function).

    Returns:
        A formatted string with the current date and time.
    """
    now = datetime.now()
    # Format similar to C#: DateTimeOffset.Now.ToString("D", null)
    # "D" format is long date pattern
    formatted_date = now.strftime("%A, %B %d, %Y")
    formatted_time = now.strftime("%I:%M:%S %p")

    return f"{formatted_date} at {formatted_time}"
