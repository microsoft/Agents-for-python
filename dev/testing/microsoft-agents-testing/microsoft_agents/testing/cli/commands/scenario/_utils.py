import json
import math

from microsoft_agents.activity import Activity
from microsoft_agents.testing.cli.core import Output
from microsoft_agents.testing.core import ActivityTemplate

def load_activity(message: str | None, json_file, out: Output) -> Activity:
    """Load an activity from a message or JSON file."""

    if not message and not json_file:
        out.error("Either --message or --json-file must be provided.", exit=True)

    if message and json_file:
        out.error("Cannot provide both --message and --json-file. Please choose one.", exit=True)

    activity: Activity
    template = ActivityTemplate().with_defaults({
        "type": "message",
        "channel_id": "test",
        "conversation.id": "test-conversation",
        "locale": "en-US",
        "from.id": "user-id",
        "from.name": "User",
        "recipient.id": "agent-id",
        "recipient.name": "Agent",
    })
    if message:
        assert isinstance(message, str)
        activity = template.create({
            "text": message
        })
    else:
        data = json.load(json_file)
        activity = template.create(data)

    return activity


def console_histogram(data, out: Output, bins: int = 10, char: str = '█'):
    """
    Prints a text-based histogram in the console.
    
    :param data: List of numeric values
    :param bins: Number of bins to group data
    :param char: Character used for bars
    """
    if not data:
        out.error("No data provided.", exit=True)
        return
    
    # Validate numeric data
    try:
        data = [float(x) for x in data]
    except ValueError:
        out.error("Data must be numeric.", exit=True)
        return

    min_val, max_val = min(data), max(data)
    if min_val == max_val:
        out.error(f"All values are the same: {min_val}", exit=True)
        return

    # Bin width
    bin_width = (max_val - min_val) / bins
    bin_counts = [0] * bins

    # Count values in bins
    for value in data:
        index = min(int((value - min_val) / bin_width), bins - 1)
        bin_counts[index] += 1

    # Find the largest count for scaling
    max_count = max(bin_counts)

    # Print histogram
    for i, count in enumerate(bin_counts):
        bar = char * math.ceil((count / max_count) * 50)  # scale to max 50 chars
        bin_start = min_val + i * bin_width
        bin_end = bin_start + bin_width
        out.info(f"{bin_start:>7.2f} - {bin_end:>7.2f} | {bar} ({count})")