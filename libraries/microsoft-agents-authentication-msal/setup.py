from os import environ
from setuptools import setup

package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    install_requires=[
        f"microsoft-agents-hosting-core=={package_version}",
        "msal>=1.31.1",
        "requests>=2.32.3",
        "cryptography>=44.0.0",
    ],
)
