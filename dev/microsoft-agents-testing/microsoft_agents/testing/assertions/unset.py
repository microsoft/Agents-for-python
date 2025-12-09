from __future__ import annotations

class Unset:
    """Singleton to represent an unset field in activity comparisons."""

    def __init__(self):
        raise RuntimeError("Unset is a singleton and cannot be instantiated.")

    @staticmethod
    def get(*args, **kwargs):
        """Returns the singleton instance."""
        return Unset