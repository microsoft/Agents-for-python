from os import environ
from setuptools import setup

package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
)
