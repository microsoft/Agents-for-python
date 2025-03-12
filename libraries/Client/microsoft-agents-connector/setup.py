from os import environ
from setuptools import setup

package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    install_requires=[
        "isodate>=0.6.1",
        "azure-core>=1.30.0",
        f"microsoft-agents-authentication=={package_version}",
        f"microsoft-agents-core=={package_version}",
    ],
)
