# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Load development tooling without adding it to SDK distributions."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/teams-api-drift"))
