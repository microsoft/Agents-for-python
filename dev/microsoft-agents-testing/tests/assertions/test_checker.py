import pytest
from pydantic import BaseModel
from microsoft_agents.testing.assertions.checker import Checker, create_base


# Test models for BaseModel testing
class Person(BaseModel):
    name: str
    age: int
    email: str | None = None


class Address(BaseModel):
    street: str
    city: str
    zip_code: str


class TestCreateBase:
    """Tests for the create_base helper function"""

    def test_create_base_with_none(self):
        """Test create_base with None returns kwargs only"""
        result = create_base(None, key1="value1", key2="value2")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_create_base_with_none_no_kwargs(self):
        """Test create_base with None and no kwargs returns empty dict"""
        result = create_base(None)
        assert result == {}

    def test_create_base_with_dict(self):
        """Test create_base with dict merges with kwargs"""
        model = {"existing": "value"}
        result = create_base(model, new="added")
        assert result == {"existing": "value", "new": "added"}

    def test_create_base_with_dict_dotted_keys(self):
        """Test create_base with dict containing dotted keys expands them"""
        model = {"parent.child": "value"}
        result = create_base(model, extra="data")
        assert result == {"parent": {"child": "value"}, "extra": "data"}

    def test_create_base_with_basemodel(self):
        """Test create_base with BaseModel converts to dict"""
        person = Person(name="Alice", age=30, email="alice@example.com")
        result = create_base(person, extra="field")
        assert result == {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com",
            "extra": "field"
        }

    def test_create_base_with_basemodel_exclude_unset(self):
        """Test create_base with BaseModel excludes unset fields"""
        person = Person(name="Bob", age=25)  # email not set
        result = create_base(person)
        assert result == {"name": "Bob", "age": 25}
        assert "email" not in result

    def test_create_base_with_callable(self):
        """Test create_base with callable stores it under __call"""
        def custom_check():
            return True
        
        result = create_base(custom_check, extra="value")
        assert result["__call"] == custom_check
        assert result["extra"] == "value"

    def test_create_base_with_lambda(self):
        """Test create_base with lambda function"""
        check = lambda x: x > 5
        result = create_base(check)
        assert result["__call"] == check

    def test_create_base_with_invalid_type(self):
        """Test create_base with invalid type raises TypeError"""
        with pytest.raises(TypeError, match="model must be a dict, BaseModel, or Callable"):
            create_base("invalid")

    def test_create_base_kwargs_override(self):
        """Test that kwargs override dict values"""
        model = {"key": "original"}
        result = create_base(model, key="overridden")
        assert result["key"] == "overridden"


class TestCheckerInit:
    """Tests for Checker initialization"""

    def test_init_with_none(self):
        """Test Checker can be initialized with None"""
        checker = Checker(None)
        assert checker._selector == {}

    def test_init_with_dict(self):
        """Test Checker initialization with dict"""
        checker = Checker({"name": "Alice"})
        assert checker._selector == {"name": "Alice"}

    def test_init_with_kwargs(self):
        """Test Checker initialization with kwargs"""
        checker = Checker(name="Alice", age=30)
        assert checker._selector == {"name": "Alice", "age": 30}

    def test_init_with_dict_and_kwargs(self):
        """Test Checker initialization with both dict and kwargs"""
        checker = Checker({"name": "Alice"}, age=30)
        assert checker._selector == {"name": "Alice", "age": 30}

    def test_init_with_basemodel(self):
        """Test Checker initialization with BaseModel"""
        person = Person(name="Alice", age=30)
        checker = Checker(person)
        assert checker._selector == {"name": "Alice", "age": 30}

    def test_init_with_callable(self):
        """Test Checker initialization with callable"""
        def check_func():
            return True
        
        checker = Checker(check_func)
        assert "__call" in checker._selector
        assert checker._selector["__call"] == check_func


class TestCheckerCheck:
    """Tests for Checker.check method"""

    def test_check_dict_exact_match(self):
        """Test check with exact dict match"""
        checker = Checker({"name": "Alice", "age": 30})
        actual = {"name": "Alice", "age": 30}
        assert checker.check(actual) is True

    def test_check_dict_no_match(self):
        """Test check with dict that doesn't match"""
        checker = Checker({"name": "Alice"})
        actual = {"name": "Bob"}
        assert checker.check(actual) is False