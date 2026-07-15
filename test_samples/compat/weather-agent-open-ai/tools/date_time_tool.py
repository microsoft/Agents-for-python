from agents import function_tool
from datetime import datetime


@function_tool
def get_date() -> str:
    """
    A function tool that returns the current date and time.
    """
    return datetime.now().isoformat()
