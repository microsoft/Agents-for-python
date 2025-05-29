import os
import sys
import importlib.metadata


def get_product_info() -> str:
    """
    Generates a string containing information about the SDK version and runtime environment.
    This is used for telemetry and User-Agent headers in HTTP requests.

    Returns:
        A formatted string containing the SDK version, Python version, and OS details
    """
    try:
        # Try to get package version from metadata
        sdk_version = importlib.metadata.version("microsoft-agents-connector")
    except importlib.metadata.PackageNotFoundError:
        # Fallback if package is not installed
        sdk_version = "unknown"

    python_version = sys.version.split()[0]
    platform = sys.platform
    architecture = os.uname().machine if hasattr(os, "uname") else "unknown"
    os_release = os.uname().release if hasattr(os, "uname") else "unknown"

    return f"agents-sdk-py/{sdk_version} python/{python_version} {platform}-{architecture}/{os_release}"
