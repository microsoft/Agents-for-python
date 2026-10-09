# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Single command-line entry point for Teams API drift tooling."""

from teams_api_drift.cli import entrypoint

if __name__ == "__main__":
    raise SystemExit(entrypoint())
