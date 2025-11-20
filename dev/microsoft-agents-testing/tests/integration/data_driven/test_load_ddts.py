# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import pytest
import tempfile
import os
from pathlib import Path

from microsoft_agents.testing.integration.data_driven import DataDrivenTest
from microsoft_agents.testing.integration.data_driven.load_ddts import load_ddts


class TestLoadDdts:
    """Tests for load_ddts function."""

    def test_load_ddts_from_empty_directory(self):
        """Test loading from an empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_ddts(temp_dir, recursive=False)
            assert result == []

    def test_load_single_json_file(self):
        """Test loading a single JSON test file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {
                "name": "test1",
                "description": "Test 1",
                "test": [{"type": "input", "activity": {"text": "Hello"}}],
            }

            json_file = Path(temp_dir) / "test1.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            result = load_ddts(temp_dir, recursive=False)

            assert len(result) == 1
            assert isinstance(result[0], DataDrivenTest)
            assert result[0]._name == "test1"

    def test_load_single_yaml_file(self):
        """Test loading a single YAML test file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_content = """name: test1
description: Test 1
test:
  - type: input
    activity:
      text: Hello
"""

            yaml_file = Path(temp_dir) / "test1.yaml"
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            result = load_ddts(temp_dir, recursive=False)

            assert len(result) == 1
            assert isinstance(result[0], DataDrivenTest)
            assert result[0]._name == "test1"

    def test_load_multiple_files(self):
        """Test loading multiple test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create JSON file
            json_data = {
                "name": "json_test",
                "test": [{"type": "input", "activity": {"text": "Hello"}}],
            }
            json_file = Path(temp_dir) / "test1.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f)

            # Create YAML file
            yaml_content = """name: yaml_test
test:
  - type: input
    activity:
      text: World
"""
            yaml_file = Path(temp_dir) / "test2.yaml"
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            result = load_ddts(temp_dir, recursive=False)

            assert len(result) == 2
            names = {test._name for test in result}
            assert "json_test" in names
            assert "yaml_test" in names

    def test_load_recursive(self):
        """Test loading files recursively from subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()

            # Create file in root
            root_data = {"name": "root_test", "test": []}
            root_file = Path(temp_dir) / "root.json"
            with open(root_file, "w", encoding="utf-8") as f:
                json.dump(root_data, f)

            # Create file in subdirectory
            sub_data = {"name": "sub_test", "test": []}
            sub_file = sub_dir / "sub.json"
            with open(sub_file, "w", encoding="utf-8") as f:
                json.dump(sub_data, f)

            # Non-recursive should find only root file
            result_non_recursive = load_ddts(temp_dir, recursive=False)
            assert len(result_non_recursive) == 1
            assert result_non_recursive[0]._name == "root_test"

            # Recursive should find both files
            result_recursive = load_ddts(temp_dir, recursive=True)
            assert len(result_recursive) == 2
            names = {test._name for test in result_recursive}
            assert "root_test" in names
            assert "sub_test" in names

    def test_load_with_parent_reference(self):
        """Test loading files with parent references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create parent file
            parent_data = {
                "name": "parent",
                "defaults": {
                    "input": {"activity": {"type": "message", "locale": "en-US"}}
                },
            }
            parent_file = Path(temp_dir) / "parent.json"
            with open(parent_file, "w", encoding="utf-8") as f:
                json.dump(parent_data, f)

            # Create child file with parent reference
            child_data = {
                "name": "child",
                "parent": str(parent_file),
                "test": [{"type": "input", "activity": {"text": "Hello"}}],
            }
            child_file = Path(temp_dir) / "child.json"
            with open(child_file, "w", encoding="utf-8") as f:
                json.dump(child_data, f)

            result = load_ddts(temp_dir, recursive=False)

            # Should load both files
            assert len(result) == 1

            # Find the child test
            child_test = next((t for t in result if t._name == "parent.child"), None)
            assert child_test is not None

            # Child should have inherited defaults from parent
            assert child_test._input_defaults == {
                "activity": {"type": "message", "locale": "en-US"}
            }

    def test_load_with_relative_parent_reference(self):
        """Test loading files with relative parent references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create parent file
            parent_data = {
                "name": "parent",
                "defaults": {"input": {"activity": {"type": "message"}}},
            }
            parent_file = Path(temp_dir) / "parent.yaml"
            with open(parent_file, "w", encoding="utf-8") as f:
                f.write(
                    "name: parent\ndefaults:\n  input:\n    activity:\n      type: message\n"
                )

            # Create child file with relative parent reference
            child_data = {"name": "child", "parent": "parent.yaml", "test": []}
            child_file = Path(temp_dir) / "child.json"
            with open(child_file, "w", encoding="utf-8") as f:
                json.dump(child_data, f)

            # Change to temp_dir so relative path works
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = load_ddts(temp_dir, recursive=False)

                assert len(result) == 1
                child_test = next((t for t in result if t._name == "parent.child"), None)
                assert child_test is not None
            finally:
                os.chdir(original_dir)

    def test_load_with_nested_parent_references(self):
        """Test loading files with nested parent references (grandparent -> parent -> child)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create grandparent file
            grandparent_data = {
                "name": "grandparent",
                "defaults": {"input": {"activity": {"type": "message"}}},
            }
            grandparent_file = Path(temp_dir) / "grandparent.json"
            with open(grandparent_file, "w", encoding="utf-8") as f:
                json.dump(grandparent_data, f)

            # Create parent file referencing grandparent
            parent_data = {
                "name": "parent",
                "parent": str(grandparent_file),
                "defaults": {"input": {"activity": {"locale": "en-US"}}},
            }
            parent_file = Path(temp_dir) / "parent.json"
            with open(parent_file, "w", encoding="utf-8") as f:
                json.dump(parent_data, f)

            # Create child file referencing parent
            child_data = {"name": "child", "parent": str(parent_file), "test": []}
            child_file = Path(temp_dir) / "child.json"
            with open(child_file, "w", encoding="utf-8") as f:
                json.dump(child_data, f)

            result = load_ddts(temp_dir, recursive=False)

            # Should load all three files
            assert len(result) == 1

            # Verify child has inherited all defaults
            child_test = next((t for t in result if t._name == "grandparent.parent.child"), None)
            assert child_test is not None

    def test_load_with_missing_parent_raises_error(self):
        """Test that referencing a non-existent parent file raises an error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create child file with non-existent parent reference
            child_data = {
                "name": "child",
                "parent": str(Path(temp_dir) / "nonexistent.json"),
                "test": [],
            }
            child_file = Path(temp_dir) / "child.json"
            with open(child_file, "w", encoding="utf-8") as f:
                json.dump(child_data, f)

            with pytest.raises(Exception):
                load_ddts(temp_dir, recursive=False)

    def test_load_sets_name_from_filename_when_missing(self):
        """Test that name is set from filename when not provided in test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file without name field
            test_data = {"test": [{"type": "input", "activity": {"text": "Hello"}}]}
            test_file = Path(temp_dir) / "my_test_file.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            result = load_ddts(temp_dir, recursive=False)

            assert len(result) == 1
            assert result[0]._name == "my_test_file"

    def test_load_uses_current_working_directory_when_path_is_none(self):
        """Test that load_ddts uses current working directory when path is None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_data = {"name": "test", "test": []}
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            # Change to temp_dir and load without path
            original_dir = os.getcwd()
            try:
                os.chdir(temp_dir)
                result = load_ddts(None, recursive=False)

                assert len(result) == 1
                assert result[0]._name == "test"
            finally:
                os.chdir(original_dir)

    def test_load_resolves_parent_to_absolute_path(self):
        """Test that parent references are resolved to absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create parent file
            parent_data = {
                "name": "parent",
                "defaults": {"input": {"activity": {"type": "message"}}},
            }
            parent_file = Path(temp_dir) / "parent.json"
            with open(parent_file, "w", encoding="utf-8") as f:
                json.dump(parent_data, f)

            # Create child with parent reference
            child_data = {"name": "child", "parent": str(parent_file), "test": []}
            child_file = Path(temp_dir) / "child.json"
            with open(child_file, "w", encoding="utf-8") as f:
                json.dump(child_data, f)

            result = load_ddts(temp_dir, recursive=False)

            # Find child and verify parent is a dict (resolved)
            child_test = next((t for t in result if t._name == "parent.child"), None)
            assert child_test is not None

    def test_load_handles_mixed_json_and_yaml_files(self):
        """Test loading both JSON and YAML files together."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create JSON parent
            parent_data = {
                "name": "json_parent",
                "defaults": {"input": {"activity": {"type": "message"}}},
            }
            parent_file = Path(temp_dir) / "parent.json"
            with open(parent_file, "w", encoding="utf-8") as f:
                json.dump(parent_data, f)

            # Create YAML child referencing JSON parent
            yaml_content = f"""name: yaml_child
parent: {parent_file}
test: []
"""
            child_file = Path(temp_dir) / "child.yaml"
            with open(child_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            result = load_ddts(temp_dir, recursive=False)

            assert len(result) == 1
            names = {test._name for test in result}
            assert "json_parent.yaml_child" in names

    def test_load_with_path_as_string(self):
        """Test that path parameter accepts string type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"name": "test", "test": []}
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            # Pass path as string instead of Path object
            result = load_ddts(str(temp_dir), recursive=False)

            assert len(result) == 1
            assert result[0]._name == "test"

    def test_load_with_path_as_path_object(self):
        """Test that path parameter accepts Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"name": "test", "test": []}
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            # Pass path as Path object
            result = load_ddts(Path(temp_dir), recursive=False)

            assert len(result) == 1
            assert result[0]._name == "test"
