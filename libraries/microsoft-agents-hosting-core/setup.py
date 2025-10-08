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
        f"microsoft-agents-activity=={package_version}",
        "pyjwt>=2.10.1",
        "isodate>=0.6.1",
        "azure-core>=1.30.0",
        "python-dotenv>=1.1.1",
    ],
)
