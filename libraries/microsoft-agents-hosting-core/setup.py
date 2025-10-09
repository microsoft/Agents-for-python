from os import environ
from setuptools import setup

package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    install_requires=[
        f"microsoft-agents-activity=={package_version}",
        "pyjwt>=2.10.1",
        "isodate>=0.6.1",
        "azure-core>=1.30.0",
        "python-dotenv>=1.1.1",
    ],
)
