from os import environ
from setuptools import setup

package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    install_requires=[
        f"microsoft-agents-connector=={package_version}",
        f"microsoft-agents-botbuilder=={package_version}",
        "aiohttp>=3.11.11",
    ],
)
