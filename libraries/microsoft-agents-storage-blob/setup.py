from os import environ, path
from setuptools import setup

# Try to read from VERSION.txt file first, fall back to environment variable
version_file = path.join(path.dirname(__file__), "VERSION.txt")
if path.exists(version_file):
    with open(version_file, "r", encoding="utf-8") as f:
        package_version = f.read().strip()
else:
    package_version = environ.get("PackageVersion", "0.0.0")

setup(
    version=package_version,
    install_requires=[
        f"microsoft-agents-hosting-core=={package_version}",
        "azure-core",
        "azure-storage-blob",
        "azure-identity",
    ],
)
