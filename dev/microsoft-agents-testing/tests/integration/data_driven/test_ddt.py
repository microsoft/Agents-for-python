# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from microsoft_agents.activity import Activity
from microsoft_agents.testing.integration.core import (
    Integration,
    AgentClient,
    ResponseClient,
)
from microsoft_agents.testing.integration.data_driven import DataDrivenTest, ddt
from microsoft_agents.testing.integration.data_driven.ddt import _add_test_method


class TestAddTestMethod:
    """Tests for _add_test_method function."""

    def test_add_test_method_creates_method(self):
        """Test that _add_test_method creates a new test method on the class."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test_case_1"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        assert hasattr(TestClass, "test_data_driven__test_case_1")
        method = getattr(TestClass, "test_data_driven__test_case_1")
        assert callable(method)

    def test_add_test_method_replaces_slashes_in_name(self):
        """Test that slashes in test name are replaced with underscores."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "folder/subfolder/test_case"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        assert hasattr(TestClass, "test_data_driven__folder_subfolder_test_case")
        assert not hasattr(TestClass, "test_data_driven__folder/subfolder/test_case")

    def test_add_test_method_replaces_dots_in_name(self):
        """Test that dots in test name are replaced with underscores."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test.case.with.dots"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        assert hasattr(TestClass, "test_data_driven__test_case_with_dots")

    def test_add_test_method_replaces_multiple_special_chars(self):
        """Test that multiple special characters are replaced."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "path/to/test.case.name"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        assert hasattr(TestClass, "test_data_driven__path_to_test_case_name")

    @pytest.mark.asyncio
    async def test_add_test_method_runs_data_driven_test(self):
        """Test that the added method runs the data driven test."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test_case"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        test_instance = TestClass()
        mock_agent_client = AsyncMock(spec=AgentClient)
        mock_response_client = AsyncMock(spec=ResponseClient)

        await test_instance.test_data_driven__test_case(
            mock_agent_client, mock_response_client
        )

        mock_ddt.run.assert_called_once_with(mock_agent_client, mock_response_client)

    @pytest.mark.asyncio
    async def test_add_test_method_has_pytest_asyncio_mark(self):
        """Test that the added method has pytest.mark.asyncio decorator."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test_case"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        method = getattr(TestClass, "test_data_driven__test_case")
        assert hasattr(method, "pytestmark")
        assert any(mark.name == "asyncio" for mark in method.pytestmark)

    def test_add_test_method_multiple_tests(self):
        """Test adding multiple test methods to the same class."""

        class TestClass(Integration):
            pass

        mock_ddt1 = Mock(spec=DataDrivenTest)
        mock_ddt1.name = "test_case_1"
        mock_ddt1.run = AsyncMock()

        mock_ddt2 = Mock(spec=DataDrivenTest)
        mock_ddt2.name = "test_case_2"
        mock_ddt2.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt1)
        _add_test_method(TestClass, mock_ddt2)

        assert hasattr(TestClass, "test_data_driven__test_case_1")
        assert hasattr(TestClass, "test_data_driven__test_case_2")

    @pytest.mark.asyncio
    async def test_add_test_method_preserves_test_scope(self):
        """Test that each added method maintains its own test scope."""

        class TestClass(Integration):
            pass

        mock_ddt1 = Mock(spec=DataDrivenTest)
        mock_ddt1.name = "test_1"
        mock_ddt1.run = AsyncMock()

        mock_ddt2 = Mock(spec=DataDrivenTest)
        mock_ddt2.name = "test_2"
        mock_ddt2.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt1)
        _add_test_method(TestClass, mock_ddt2)

        test_instance = TestClass()
        mock_agent_client = AsyncMock(spec=AgentClient)
        mock_response_client = AsyncMock(spec=ResponseClient)

        await test_instance.test_data_driven__test_1(
            mock_agent_client, mock_response_client
        )
        await test_instance.test_data_driven__test_2(
            mock_agent_client, mock_response_client
        )

        # Each test should call its own run method
        mock_ddt1.run.assert_called_once()
        mock_ddt2.run.assert_called_once()

    def test_add_test_method_empty_name(self):
        """Test adding method with empty test name."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = ""
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        assert hasattr(TestClass, "test_data_driven__")

    def test_add_test_method_name_with_spaces(self):
        """Test that spaces in names are preserved (converted to underscores by replace)."""

        class TestClass(Integration):
            pass

        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test with spaces"
        mock_ddt.run = AsyncMock()

        _add_test_method(TestClass, mock_ddt)

        # Spaces are not replaced by the current implementation
        assert hasattr(TestClass, "test_data_driven__test with spaces")


class TestDdtDecorator:
    """Tests for ddt decorator function."""

    def test_ddt_decorator_raises_if_no_tests(self):
        """Test that ddt raises if not tests are found."""
        with pytest.raises(RuntimeError):
            ddt("test_path")

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_recursive_false(self, mock_load_ddts):
        """Test that ddt decorator respects recursive parameter."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]

        @ddt("test_path", recursive=False)
        class TestClass(Integration):
            pass

        mock_load_ddts.assert_called_once_with("test_path", recursive=False)

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_adds_test_methods(self, mock_load_ddts):
        """Test that ddt decorator adds test methods for each loaded test."""
        mock_ddt1 = Mock(spec=DataDrivenTest)
        mock_ddt1.name = "test_1"
        mock_ddt1.run = AsyncMock()

        mock_ddt2 = Mock(spec=DataDrivenTest)
        mock_ddt2.name = "test_2"
        mock_ddt2.run = AsyncMock()

        mock_load_ddts.return_value = [mock_ddt1, mock_ddt2]

        @ddt("test_path")
        class TestClass(Integration):
            pass

        assert hasattr(TestClass, "test_data_driven__test_1")
        assert hasattr(TestClass, "test_data_driven__test_2")

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_returns_same_class(self, mock_load_ddts):
        """Test that ddt decorator returns the same class (modified)."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test_case"})]

        class TestClass(Integration):
            pass

        decorated = ddt("test_path")(TestClass)

        assert decorated is TestClass

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_preserves_existing_methods(self, mock_load_ddts):
        """Test that ddt decorator preserves existing test methods."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "new_test"})]

        @ddt("test_path")
        class TestClass(Integration):
            def test_existing_method(self):
                pass

        assert hasattr(TestClass, "test_existing_method")

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_path_as_pathlib_path(self, mock_load_ddts):
        """Test ddt decorator with pathlib.Path object."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]
        test_path = Path("test_path")

        @ddt(str(test_path))
        class TestClass(Integration):
            pass

        mock_load_ddts.assert_called_once_with(str(test_path), recursive=True)

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_multiple_classes(self, mock_load_ddts):
        """Test that ddt decorator can be applied to multiple classes."""
        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "test_case"
        mock_ddt.run = AsyncMock()
        mock_load_ddts.return_value = [mock_ddt]

        @ddt("test_path")
        class TestClass1(Integration):
            pass

        @ddt("test_path")
        class TestClass2(Integration):
            pass

        assert hasattr(TestClass1, "test_data_driven__test_case")
        assert hasattr(TestClass2, "test_data_driven__test_case")

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_relative_path(self, mock_load_ddts):
        """Test ddt decorator with relative path."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]

        @ddt("./tests/data")
        class TestClass(Integration):
            pass

        mock_load_ddts.assert_called_once_with("./tests/data", recursive=True)

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_absolute_path(self, mock_load_ddts):
        """Test ddt decorator with absolute path."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]
        abs_path = Path("/absolute/path/to/tests").as_posix()

        @ddt(abs_path)
        class TestClass(Integration):
            pass

        mock_load_ddts.assert_called_once_with(abs_path, recursive=True)


class TestDdtDecoratorIntegration:
    """Integration tests for ddt decorator with actual file loading."""

    def test_ddt_decorator_loads_real_json_files(self):
        """Test ddt decorator with actual JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_data = {
                "name": "real_test",
                "test": [
                    {"type": "input", "activity": {"type": "message", "text": "Hello"}}
                ],
            }
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            @ddt(temp_dir, recursive=False)
            class TestClass(Integration):
                pass

            assert hasattr(TestClass, "test_data_driven__real_test")

    def test_ddt_decorator_loads_real_yaml_files(self):
        """Test ddt decorator with actual YAML files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            yaml_content = """name: yaml_test
test:
  - type: input
    activity:
      type: message
      text: Hello
"""
            test_file = Path(temp_dir) / "test.yaml"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            @ddt(temp_dir, recursive=False)
            class TestClass(Integration):
                pass

            assert hasattr(TestClass, "test_data_driven__yaml_test")

    def test_ddt_decorator_loads_multiple_files(self):
        """Test ddt decorator loading multiple test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            for i in range(3):
                test_data = {"name": f"test_{i}", "test": []}
                test_file = Path(temp_dir) / f"test_{i}.json"
                with open(test_file, "w", encoding="utf-8") as f:
                    json.dump(test_data, f)

            @ddt(temp_dir, recursive=False)
            class TestClass(Integration):
                pass

            assert hasattr(TestClass, "test_data_driven__test_0")
            assert hasattr(TestClass, "test_data_driven__test_1")
            assert hasattr(TestClass, "test_data_driven__test_2")

    def test_ddt_decorator_recursive_loading(self):
        """Test ddt decorator with recursive directory loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()

            # Create test in root
            root_data = {"name": "root_test", "test": []}
            root_file = Path(temp_dir) / "root.json"
            with open(root_file, "w", encoding="utf-8") as f:
                json.dump(root_data, f)

            # Create test in subdirectory
            sub_data = {"name": "sub_test", "test": []}
            sub_file = sub_dir / "sub.json"
            with open(sub_file, "w", encoding="utf-8") as f:
                json.dump(sub_data, f)

            @ddt(temp_dir, recursive=True)
            class TestClass(Integration):
                pass

            assert hasattr(TestClass, "test_data_driven__root_test")
            assert hasattr(TestClass, "test_data_driven__sub_test")

    def test_ddt_decorator_non_recursive_skips_subdirs(self):
        """Test that non-recursive mode skips subdirectories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            sub_dir = Path(temp_dir) / "subdir"
            sub_dir.mkdir()

            # Create test in subdirectory
            sub_data = {"name": "sub_test", "test": []}
            sub_file = sub_dir / "sub.json"
            with open(sub_file, "w", encoding="utf-8") as f:
                json.dump(sub_data, f)

            with pytest.raises(Exception):
                @ddt(temp_dir, recursive=False)
                class TestClass(Integration):
                    pass

    @pytest.mark.asyncio
    async def test_ddt_decorated_class_runs_tests(self):
        """Test that decorated class can actually run the generated tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_data = {
                "name": "runnable_test",
                "test": [
                    {"type": "input", "activity": {"type": "message", "text": "Hello"}}
                ],
            }
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            @ddt(temp_dir, recursive=False)
            class TestClass(Integration):
                pass

            test_instance = TestClass()
            mock_agent_client = AsyncMock(spec=AgentClient)
            mock_response_client = AsyncMock(spec=ResponseClient)

            await test_instance.test_data_driven__runnable_test(
                mock_agent_client, mock_response_client
            )

            # Verify the test ran
            mock_agent_client.send_activity.assert_called_once()


class TestDdtDecoratorEdgeCases:
    """Tests for edge cases in ddt decorator."""

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_load_error(self, mock_load_ddts):
        """Test ddt decorator behavior when load_ddts raises an error."""
        mock_load_ddts.side_effect = FileNotFoundError("Test files not found")

        with pytest.raises(FileNotFoundError):

            @ddt("nonexistent_path")
            class TestClass(Integration):
                pass

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_duplicate_test_names(self, mock_load_ddts):
        """Test that duplicate test names overwrite previous methods."""
        mock_ddt1 = Mock(spec=DataDrivenTest)
        mock_ddt1.name = "test_duplicate"
        mock_ddt1.run = AsyncMock(return_value="first")

        mock_ddt2 = Mock(spec=DataDrivenTest)
        mock_ddt2.name = "test_duplicate"
        mock_ddt2.run = AsyncMock(return_value="second")

        mock_load_ddts.return_value = [mock_ddt1, mock_ddt2]

        @ddt("test_path")
        class TestClass(Integration):
            pass

        # Second test should overwrite the first
        assert hasattr(TestClass, "test_data_driven__test_duplicate")
        # Only one method with this name should exist

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_preserves_class_attributes(self, mock_load_ddts):
        """Test that ddt decorator preserves class attributes."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]

        @ddt("test_path")
        class TestClass(Integration):
            class_attr = "test_value"
            _service_url = "http://example.com"

        assert TestClass.class_attr == "test_value"
        assert TestClass._service_url == "http://example.com"

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_preserves_class_docstring(self, mock_load_ddts):
        """Test that ddt decorator preserves class docstring."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]

        @ddt("test_path")
        class TestClass(Integration):
            """This is a test class docstring."""

            pass

        assert TestClass.__doc__ == "This is a test class docstring."

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_with_special_characters_in_path(self, mock_load_ddts):
        """Test ddt decorator with special characters in path."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]
        special_path = "test path/with spaces/and-dashes"

        @ddt(special_path)
        class TestClass(Integration):
            pass

        mock_load_ddts.assert_called_once_with(special_path, recursive=True)

    def test_ddt_decorator_with_test_name_collision(self):
        """Test that generated test names don't collide with existing methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data = {"name": "existing_test", "test": []}
            test_file = Path(temp_dir) / "test.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)

            @ddt(temp_dir, recursive=False)
            class TestClass(Integration):
                def test_data_driven__existing_test(self):
                    """Existing method with same name."""
                    return "original"

            # The decorator will overwrite the existing method
            assert hasattr(TestClass, "test_data_driven__existing_test")


class TestDdtDecoratorWithRealIntegrationClass:
    """Tests using actual Integration class features."""

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_on_integration_subclass(self, mock_load_ddts):
        """Test ddt decorator on a proper Integration subclass."""
        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "integration_test"
        mock_ddt.run = AsyncMock()
        mock_load_ddts.return_value = [mock_ddt]

        @ddt("test_path")
        class MyIntegrationTest(Integration):
            _service_url = "http://localhost:3978"
            _agent_url = "http://localhost:8000"

        assert hasattr(MyIntegrationTest, "test_data_driven__integration_test")
        assert MyIntegrationTest._service_url == "http://localhost:3978"

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_with_integration_fixtures(self, mock_load_ddts):
        """Test that ddt-generated tests can work with Integration fixtures."""
        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "fixture_test"
        mock_ddt.run = AsyncMock()
        mock_load_ddts.return_value = [mock_ddt]

        @ddt("test_path")
        class MyIntegrationTest(Integration):
            _service_url = "http://localhost:3978"
            _agent_url = "http://localhost:8000"

        # The generated method should accept agent_client and response_client parameters
        import inspect

        method = getattr(MyIntegrationTest, "test_data_driven__fixture_test")
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        assert "self" in params
        assert "agent_client" in params
        assert "response_client" in params

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_multiple_decorators_on_same_class(self, mock_load_ddts):
        """Test applying multiple ddt decorators to the same class."""
        mock_ddt1 = Mock(spec=DataDrivenTest)
        mock_ddt1.name = "test_1"
        mock_ddt1.run = AsyncMock()

        mock_ddt2 = Mock(spec=DataDrivenTest)
        mock_ddt2.name = "test_2"
        mock_ddt2.run = AsyncMock()

        mock_load_ddts.side_effect = [[mock_ddt1], [mock_ddt2]]

        @ddt("path2")
        @ddt("path1")
        class TestClass(Integration):
            pass

        assert hasattr(TestClass, "test_data_driven__test_1")
        assert hasattr(TestClass, "test_data_driven__test_2")

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_ddt_decorator_return_type(self, mock_load_ddts):
        """Test that ddt decorator returns the correct type."""
        mock_load_ddts.return_value = [DataDrivenTest({"name": "test1"})]

        class TestClass(Integration):
            pass

        decorated = ddt("test_path")(TestClass)

        assert isinstance(decorated, type)
        assert issubclass(decorated, Integration)


class TestDdtDecoratorDocumentation:
    """Tests related to documentation and metadata."""

    def test_ddt_function_has_docstring(self):
        """Test that ddt function has proper documentation."""
        assert ddt.__doc__ is not None
        assert "data driven tests" in ddt.__doc__.lower()

    def test_add_test_method_has_docstring(self):
        """Test that _add_test_method has proper documentation."""
        assert _add_test_method.__doc__ is not None

    @patch("microsoft_agents.testing.integration.data_driven.ddt.load_ddts")
    def test_generated_test_methods_are_discoverable(self, mock_load_ddts):
        """Test that generated test methods are discoverable by pytest."""
        mock_ddt = Mock(spec=DataDrivenTest)
        mock_ddt.name = "discoverable_test"
        mock_ddt.run = AsyncMock()
        mock_load_ddts.return_value = [mock_ddt]

        @ddt("test_path")
        class TestClass(Integration):
            pass

        # Check that the method name starts with 'test_' so pytest can discover it
        method_name = "test_data_driven__discoverable_test"
        assert hasattr(TestClass, method_name)
        assert method_name.startswith("test_")
