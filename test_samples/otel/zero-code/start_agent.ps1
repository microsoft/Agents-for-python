$ErrorActionPreference = "Stop"

uv run --env-file .env -- opentelemetry-instrument python -m src.main
