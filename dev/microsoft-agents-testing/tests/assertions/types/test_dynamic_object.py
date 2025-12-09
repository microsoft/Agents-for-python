import pytest

from microsoft_agents.testing import Unset, DynamicObject


class TestDynamicObjectPrimitives:
    """Test DynamicObject with primitive types."""
    
    def test_int_returns_int(self):
        result = DynamicObject(42)
        assert result == 42
        assert isinstance(result, int)
        assert not isinstance(result, DynamicObject)
    
    def test_float_returns_float(self):
        result = DynamicObject(3.14)
        assert result == 3.14
        assert isinstance(result, float)
        assert not isinstance(result, DynamicObject)
    
    def test_str_returns_str(self):
        result = DynamicObject("hello")
        assert result == "hello"
        assert isinstance(result, str)
        assert not isinstance(result, DynamicObject)
    
    def test_bool_returns_bool(self):
        result_true = DynamicObject(True)
        result_false = DynamicObject(False)
        assert result_true is True
        assert result_false is False
        assert isinstance(result_true, bool)
        assert not isinstance(result_true, DynamicObject)
    
    def test_none_returns_none(self):
        result = DynamicObject(None)
        assert result is None
        assert not isinstance(result, DynamicObject)
    
    def test_unset_returns_unset(self):
        result = DynamicObject(Unset)
        assert result is Unset
        assert not isinstance(result, DynamicObject)


class TestDynamicObjectDict:
    """Test DynamicObject with dictionary values."""
    
    def test_dict_creates_dynamic_object(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert isinstance(obj, DynamicObject)
    
    def test_getattr_on_dict(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert obj.name == "John"
        assert obj.age == 30
    
    def test_getattr_missing_returns_unset(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        result = obj.missing_field
        assert result is Unset
    
    def test_getitem_on_dict(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert obj["name"] == "John"
        assert obj["age"] == 30
    
    def test_getitem_missing_returns_unset(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        result = obj["missing_key"]
        assert result is Unset
    
    def test_nested_dict_access(self):
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        obj = DynamicObject(data)
        assert obj["user"]["profile"]["name"] == "John"
        assert obj["user"]["profile"]["age"] == 30


class TestDynamicObjectCustomClass:
    """Test DynamicObject with custom class instances."""
    
    def test_custom_class_creates_dynamic_object(self):
        class Person:
            def __init__(self):
                self.name = "John"
                self.age = 30
        
        person = Person()
        obj = DynamicObject(person)
        assert isinstance(obj, DynamicObject)
    
    def test_getattr_on_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
                self.age = 30
        
        person = Person()
        obj = DynamicObject(person)
        assert obj.name == "John"
        assert obj.age == 30
    
    def test_getattr_missing_on_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
        
        person = Person()
        obj = DynamicObject(person)
        result = obj.missing_attr
        assert result is Unset

class TestDynamicObjectList:
    """Test DynamicObject with list values."""
    
    def test_list_creates_dynamic_object(self):
        data = [1, 2, 3]
        obj = DynamicObject(data)
        assert isinstance(obj, DynamicObject)
    
    def test_getitem_on_list(self):
        data = ["a", "b", "c"]
        obj = DynamicObject(data)
        # Note: lists don't have .get() method, so __getitem__ will fail
        # This tests the actual behavior
        with pytest.raises(AttributeError):
            obj[0]


class TestDynamicObjectResolve:
    """Test the resolve method."""
    
    def test_resolve_dict(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert obj.resolve() == data
        assert obj.resolve() is data
    
    def test_resolve_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
        
        person = Person()
        obj = DynamicObject(person)
        assert obj.resolve() is person
    
    def test_resolve_nested(self):
        data = {"user": {"name": "John"}}
        obj = DynamicObject(data)
        user_obj = obj["user"]
        assert user_obj.resolve() == {"name": "John"}


class TestDynamicObjectEquality:
    """Test equality comparisons."""
    
    def test_equality_with_same_value(self):
        data1 = {"name": "John"}
        data2 = {"name": "John"}
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        assert obj1 == obj2
    
    def test_equality_with_different_value(self):
        data1 = {"name": "John"}
        data2 = {"name": "Jane"}
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        assert obj1 != obj2
    
    def test_equality_with_raw_value(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        assert obj == data
        assert data == obj
    
    def test_equality_with_primitive(self):
        # Primitives are returned as-is, so comparison is direct
        obj = DynamicObject(42)
        assert obj == 42


class TestDynamicObjectContains:
    """Test the __in__ method."""
    
    def test_in_with_dynamic_object(self):
        data1 = [1, 2, 3]
        data2 = 2
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        # Note: __in__ is actually called on the container, not the item
        # The method should be __contains__, but __in__ doesn't work this way
        # This test documents the actual behavior
        assert obj2 in obj1
    
    def test_in_with_raw_value(self):
        data = [1, 2, 3]
        obj = DynamicObject(data)
        obj_item = DynamicObject(2)
        assert obj_item in data


class TestDynamicObjectStringRepresentation:
    """Test string representations."""
    
    def test_str(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        assert str(obj) == str(data)
    
    def test_repr(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        assert repr(obj) == f"DynamicObject({data!r})"
    
    def test_str_with_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
            
            def __str__(self):
                return f"Person({self.name})"
        
        person = Person()
        obj = DynamicObject(person)
        assert str(obj) == "Person(John)"


class TestDynamicObjectReadonly:
    """Test that DynamicObject inherits readonly behavior."""
    
    def test_cannot_set_attribute(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        with pytest.raises(AttributeError, match="Cannot set attribute"):
            obj.new_attr = "value"
    
    def test_cannot_delete_attribute(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        with pytest.raises(AttributeError, match="Cannot delete attribute"):
            del obj.name
    
    def test_cannot_set_item(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        with pytest.raises(AttributeError, match="Cannot set item"):
            obj["new_key"] = "value"
    
    def test_cannot_delete_item(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        with pytest.raises(AttributeError, match="Cannot delete item"):
            del obj["name"]


class TestDynamicObjectChaining:
    """Test chaining of attribute/item access."""
    
    def test_chaining_all_exist(self):
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        obj = DynamicObject(data)
        result = obj["level1"]["level2"]["level3"]
        assert result == "value"
    
    def test_chaining_with_missing(self):
        data = {
            "level1": {
                "level2": {}
            }
        }
        obj = DynamicObject(data)
        result = obj["level1"]["level2"]["missing"]["nested"]
        assert result is Unset
    
    def test_mixed_getattr_getitem(self):
        class Container:
            def __init__(self):
                self.data = {"key": "value"}
        
        container = Container()
        obj = DynamicObject(container)
        result = obj.data["key"]
        assert result == "value"


class TestDynamicObjectEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_dict(self):
        obj = DynamicObject({})
        assert isinstance(obj, DynamicObject)
        assert obj.resolve() == {}
    
    def test_empty_string(self):
        result = DynamicObject("")
        assert result == ""
        assert isinstance(result, str)
    
    def test_zero(self):
        result = DynamicObject(0)
        assert result == 0
        assert isinstance(result, int)
    
    def test_nested_dynamic_objects(self):
        inner = {"value": 42}
        outer = {"inner": inner}
        obj = DynamicObject(outer)
        inner_obj = obj["inner"]
        assert isinstance(inner_obj, DynamicObject)
        assert inner_obj.resolve() == inner
    
    def test_complex_nested_structure(self):
        data = {
            "users": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ],
            "count": 2
        }
        obj = DynamicObject(data)
        assert obj["count"] == 2
        users = obj["users"]
        assert isinstance(users, DynamicObject)
        # Note: list indexing won't work due to lack of .get() method