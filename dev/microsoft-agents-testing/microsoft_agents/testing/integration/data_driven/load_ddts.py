# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json, yaml
from glob import glob
from pathlib import Path
from .data_driven_test import DataDrivenTest

def _resolve_parent(path: str, test_modules: dict) -> None:
    """Resolve the parent test flow for a given test flow data.

    :param data: The test flow data.
    :param tests: A dictionary of all test flows keyed by their file paths.
    """

    module = test_modules[str(path)]
    parent_field = module.get("parent")
    if parent_field and isinstance(parent_field, str):
        # resolve a parent path reference to the data itself
        parent_path = Path(path).parent / parent_field
        parent_path_str = str(parent_path)
        if parent_path_str not in test_modules:
            raise RuntimeError("Parent module not found in tests collection.")
        module["parent"] = test_modules[parent_path_str]

_resolve_name_seen_set = set()

def _resolve_name(module: dict) -> str:
    """Resolve the name for a given test flow data.

    :param data: The test flow data.
    :param tests: A dictionary of all test flows keyed by their file paths.
    :return: The resolved name.
    """

    if id(module) in _resolve_name_seen_set:
        return module.get("name", module["path"])
    _resolve_name_seen_set.add(id(module))

    parent = module.get("parent")
    if parent:
        return f"{_resolve_name(parent)}.{module.get('name', module['path'])}"
    else:
        return module.get("name", module["path"])

def load_ddts(
    path: str | Path | None = None, recursive: bool = False, prefix: str = ""
) -> list[DataDrivenTest]:
    """Load data driven tests from JSON and YAML files in a given path.

    :param path: The path to load test files from. If None, the current working directory is used.
    :param recursive: Whether to search for test files recursively in subdirectories.
    :return: A list of DataDrivenTest instances.
    """

    if not path:
        path = Path.cwd()

    # collect test file paths
    if recursive:
        json_file_paths = glob(f"{path}/**/*.json", recursive=True)
        yaml_file_paths = glob(f"{path}/**/*.yaml", recursive=True)
    else:
        json_file_paths = glob(f"{path}/*.json")
        yaml_file_paths = glob(f"{path}/*.yaml")

    # load files
    tests_json = dict()
    for json_file_path in json_file_paths:
        with open(json_file_path, "r", encoding="utf-8") as f:
            tests_json[str(Path(json_file_path).absolute())] = json.load(f)

    tests_yaml = dict()
    for yaml_file_path in yaml_file_paths:
        with open(yaml_file_path, "r", encoding="utf-8") as f:
            tests_yaml[str(Path(yaml_file_path).absolute())] = yaml.safe_load(f)

    test_modules = {**tests_json, **tests_yaml}

    for file_path, module in test_modules.items():
        _resolve_parent(file_path, test_modules)
        module["path"] = Path(file_path).stem  # store path for name resolution
    for file_path, module in test_modules.items():
        module["name"] = _resolve_name(module)
        if prefix:
            module["name"] = f"{prefix}.{module['name']}"

    return [DataDrivenTest(test_flow=data) for data in test_modules.values() if "test" in data]
