# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json, yaml
from glob import glob
from pathlib import Path
from .data_driven_test import DataDrivenTest


def _resolve_parent(original_path: str, data: dict, tests: dict) -> None:
    """Resolve the parent test flow for a given test flow data.

    :param data: The test flow data.
    :param tests: A dictionary of all test flows keyed by their file paths.
    """

    parent = data.get("parent")
    if parent and isinstance(parent, str):

        path = Path(original_path).parent / parent
        abs_path = path.absolute()
        data["parent"] = str(abs_path)
        if abs_path not in tests:
            if abs_path.suffix in [".json", ".yaml"]:
                with open(abs_path, "r", encoding="utf-8") as f:
                    if abs_path.suffix == ".json":
                        parent_data = json.load(f)
                    else:
                        parent_data = yaml.safe_load(f)
                    tests[str(abs_path)] = parent_data
                    if parent_data.get("parent") and isinstance(
                        parent_data.get("parent"), str
                    ):
                        _resolve_parent(parent_data, tests)


def load_ddts(
    path: str | Path | None = None, recursive: bool = False
) -> list[DataDrivenTest]:
    """Load data driven tests from JSON and YAML files in a given path.

    :param path: The path to load test files from. If None, the current working directory is used.
    :param recursive: Whether to search for test files recursively in subdirectories.
    :return: A list of DataDrivenTest instances.
    """

    if not path:
        path = Path.cwd()

    if recursive:
        json_file_paths = glob(f"{path}/**/*.json", recursive=True)
        yaml_file_paths = glob(f"{path}/**/*.yaml", recursive=True)
    else:
        json_file_paths = glob(f"{path}/*.json")
        yaml_file_paths = glob(f"{path}/*.yaml")

    tests_json = dict()
    for json_file_path in json_file_paths:
        with open(json_file_path, "r", encoding="utf-8") as f:
            tests_json[str(Path(json_file_path).absolute())] = json.load(f)

    tests_yaml = dict()
    for yaml_file_path in yaml_file_paths:
        with open(yaml_file_path, "r", encoding="utf-8") as f:
            tests_yaml[str(Path(yaml_file_path).absolute())] = yaml.safe_load(f)

    tests = {**tests_json, **tests_yaml}

    for file_path, data in tests.items():
        _resolve_parent(file_path, data, tests)

    for file_path, data in tests.items():
        # resolve parent data references
        if "parent" in data and isinstance(data["parent"], str):
            parent_data = tests.get(data["parent"])
            if not parent_data:
                raise ValueError(
                    f"Parent test flow '{data['parent']}' not found for test flow '{file_path}'"
                )
            data["parent"] = parent_data

        # ensure name is set
        if "name" not in data or not data["name"]:
            data["name"] = Path(file_path).stem

    return [DataDrivenTest(test_flow=data) for data in tests.values() if "test" in data]
