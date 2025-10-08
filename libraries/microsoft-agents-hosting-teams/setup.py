from os import environ
from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "readme.md").read_text()
package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        f"microsoft-agents-hosting-core=={package_version}",
        "aiohttp>=3.11.11",
    ],
)
