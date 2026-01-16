import pytest

from microsoft_agents.testing import (
    SafeObject,
    resolve,
    parent,
    Unset
)

class TestSafeObjectPrimitives:
    """Test SafeObject with primitive types."""
    
    def test_int_wrapping(self):
        obj = SafeObject(42)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == 42
    
    def test_float_wrapping(self):
        obj = SafeObject(3.14)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == 3.14
    
    def test_str_wrapping(self):
        obj = SafeObject("hello")
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == "hello"
    
    def test_bool_wrapping(self):
        obj_true = SafeObject(True)
        obj_false = SafeObject(False)
        assert isinstance(obj_true, SafeObject)
        assert isinstance(obj_false, SafeObject)
        assert resolve(obj_true) is True
        assert resolve(obj_false) is False
    
    def test_none_wrapping(self):
        obj = SafeObject(None)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) is None
    
    def test_unset_wrapping(self):
        obj = SafeObject(Unset)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) is Unset


class TestSafeObjectDict:
    """Test SafeObject with dictionary values."""
    
    def test_dict_creates_safe_object(self):
        data = {"name": "John", "age": 30}
        obj = SafeObject(data)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == data
    
    def test_getattr_on_dict(self):
        data = {"name": "John", "age": 30}
        obj = SafeObject(data)
        name = obj.name
        age = obj.age
        assert isinstance(name, SafeObject)
        assert isinstance(age, SafeObject)
        assert resolve(name) == "John"
        assert resolve(age) == 30
    
    def test_getattr_missing_returns_unset(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        result = obj.missing_field
        assert isinstance(result, SafeObject)
        assert resolve(result) is Unset
    
    def test_getitem_on_dict(self):
        data = {"name": "John", "age": 30}
        obj = SafeObject(data)
        name = obj["name"]
        age = obj["age"]
        assert isinstance(name, SafeObject)
        assert isinstance(age, SafeObject)
        assert resolve(name) == "John"
        assert resolve(age) == 30
    
    def test_getitem_missing_returns_unset(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        result = obj["missing_key"]
        assert isinstance(result, SafeObject)
        assert resolve(result) is Unset
    
    def test_nested_dict_access(self):
        data = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        obj = SafeObject(data)
        name = obj["user"]["profile"]["name"]
        age = obj["user"]["profile"]["age"]
        assert isinstance(name, SafeObject)
        assert isinstance(age, SafeObject)
        assert resolve(name) == "John"
        assert resolve(age) == 30


class TestSafeObjectCustomClass:
    """Test SafeObject with custom class instances."""
    
    def test_custom_class_creates_safe_object(self):
        class Person:
            def __init__(self):
                self.name = "John"
                self.age = 30
        
        person = Person()
        obj = SafeObject(person)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) is person
    
    def test_getattr_on_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
                self.age = 30
        
        person = Person()
        obj = SafeObject(person)
        name = obj.name
        age = obj.age
        assert isinstance(name, SafeObject)
        assert isinstance(age, SafeObject)
        assert resolve(name) == "John"
        assert resolve(age) == 30
    
    def test_getattr_missing_on_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
        
        person = Person()
        obj = SafeObject(person)
        result = obj.missing_attr
        assert isinstance(result, SafeObject)
        assert resolve(result) is Unset


class TestSafeObjectList:
    """Test SafeObject with list values."""
    
    def test_list_creates_safe_object(self):
        data = [1, 2, 3]
        obj = SafeObject(data)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == data
    
    def test_getitem_on_list(self):
        data = ["a", "b", "c"]
        obj = SafeObject(data)
        item0 = obj[0]
        item1 = obj[1]
        item2 = obj[2]
        assert isinstance(item0, SafeObject)
        assert isinstance(item1, SafeObject)
        assert isinstance(item2, SafeObject)
        assert resolve(item0) == "a"
        assert resolve(item1) == "b"
        assert resolve(item2) == "c"
    
    def test_getitem_negative_index(self):
        data = ["a", "b", "c"]
        obj = SafeObject(data)
        last = obj[-1]
        assert isinstance(last, SafeObject)
        assert resolve(last) == "c"
    
    def test_getitem_out_of_bounds(self):
        data = ["a", "b", "c"]
        obj = SafeObject(data)
        with pytest.raises(IndexError):
            obj[10]
    
    def test_list_of_dicts(self):
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        obj = SafeObject(data)
        first = obj[0]
        assert isinstance(first, SafeObject)
        name = first["name"]
        assert resolve(name) == "John"


class TestSafeObjectResolveFunction:
    """Test the resolve function."""
    
    def test_resolve_safe_object(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        assert resolve(obj) == data
        assert resolve(obj) is data
    
    def test_resolve_non_safe_object(self):
        value = 42
        assert resolve(value) == 42
        assert resolve(value) is value
    
    def test_resolve_string(self):
        value = "hello"
        assert resolve(value) == "hello"
    
    def test_resolve_none(self):
        assert resolve(None) is None
    
    def test_resolve_nested_safe_object(self):
        data = {"user": {"name": "John"}}
        obj = SafeObject(data)
        user_obj = obj["user"]
        assert resolve(user_obj) == {"name": "John"}


class TestSafeObjectParentTracking:
    """Test parent tracking functionality."""
    
    def test_root_has_no_parent(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        assert parent(obj) is None
    
    def test_child_has_parent(self):
        data = {"user": {"name": "John"}}
        obj = SafeObject(data)
        user_obj = obj["user"]
        assert parent(user_obj) is obj
    
    def test_grandchild_has_parent(self):
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        obj = SafeObject(data)
        level2_obj = obj["level1"]["level2"]
        level3_obj = level2_obj["level3"]
        assert parent(level3_obj) is level2_obj
        assert parent(level2_obj) is not obj  # level2 parent is level1, not root
    
    def test_parent_chain(self):
        data = {"a": {"b": {"c": "value"}}}
        obj = SafeObject(data)
        a_obj = obj["a"]
        b_obj = a_obj["b"]
        c_obj = b_obj["c"]
        
        assert parent(c_obj) is b_obj
        assert parent(b_obj) is a_obj
        assert parent(a_obj) is obj
        assert parent(obj) is None
    
    def test_parent_not_set_when_parent_value_is_none(self):
        parent_obj = SafeObject(None)
        child_obj = SafeObject("child", parent_obj)
        assert parent(child_obj) is None
    
    def test_parent_not_set_when_parent_value_is_unset(self):
        parent_obj = SafeObject(Unset)
        child_obj = SafeObject("child", parent_obj)
        assert parent(child_obj) is None


class TestSafeObjectNew:
    """Test __new__ behavior."""
    
    def test_wrapping_safe_object_returns_same(self):
        obj1 = SafeObject(42)
        obj2 = SafeObject(obj1)
        assert obj2 is obj1
    
    def test_wrapping_safe_object_ignores_parent(self):
        parent_obj = SafeObject({"key": "value"})
        obj1 = SafeObject(42)
        obj2 = SafeObject(obj1, parent_obj)
        assert obj2 is obj1
        assert parent(obj2) is None  # Original parent is preserved


class TestSafeObjectStringRepresentation:
    """Test string representations."""
    
    def test_str_with_dict(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        assert str(obj) == str(data)
    
    def test_str_with_primitive(self):
        obj = SafeObject(42)
        assert str(obj) == "42"
    
    def test_str_with_unset(self):
        obj = SafeObject(Unset)
        assert str(obj) == "Unset"
    
    def test_repr(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        assert repr(obj) == f"SafeObject({data!r})"
    
    def test_repr_with_primitive(self):
        obj = SafeObject(42)
        assert repr(obj) == "SafeObject(42)"
    
    def test_str_with_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
            
            def __str__(self):
                return f"Person({self.name})"
        
        person = Person()
        obj = SafeObject(person)
        assert str(obj) == "Person(John)"


class TestSafeObjectReadonly:
    """Test that SafeObject inherits readonly behavior."""
    
    def test_cannot_set_attribute(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError, match="Cannot set attribute"):
            obj.new_attr = "value"
    
    def test_cannot_delete_attribute(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError, match="Cannot delete attribute"):
            del obj.name
    
    def test_cannot_set_item(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError, match="Cannot set item"):
            obj["new_key"] = "value"
    
    def test_cannot_delete_item(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError, match="Cannot delete item"):
            del obj["name"]
    
    def test_cannot_modify_internal_value(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError):
            obj.__value__ = "new_value"
    
    def test_cannot_modify_internal_parent(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        with pytest.raises(AttributeError):
            obj.__parent__ = None


class TestSafeObjectChaining:
    """Test chaining of attribute/item access."""
    
    def test_chaining_all_exist(self):
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        obj = SafeObject(data)
        result = obj["level1"]["level2"]["level3"]
        assert isinstance(result, SafeObject)
        assert resolve(result) == "value"
    
    def test_chaining_with_missing(self):
        data = {
            "level1": {
                "level2": {}
            }
        }
        obj = SafeObject(data)
        result = obj["level1"]["level2"]["missing"]["nested"]
        # SafeObject should handle missing gracefully
        assert isinstance(result, SafeObject)
        assert resolve(result) is Unset
    
    def test_mixed_getattr_getitem(self):
        class Container:
            def __init__(self):
                self.data = {"key": "value"}
        
        container = Container()
        obj = SafeObject(container)
        result = obj.data["key"]
        assert isinstance(result, SafeObject)
        assert resolve(result) == "value"
    
    def test_chaining_through_unset(self):
        data = {"level1": {}}
        obj = SafeObject(data)
        result = obj["level1"]["missing"]["deep"]["nested"]
        # Should chain through Unset values
        assert isinstance(result, SafeObject)
        assert resolve(result) is Unset


class TestSafeObjectEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_dict(self):
        obj = SafeObject({})
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == {}
    
    def test_empty_string(self):
        obj = SafeObject("")
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == ""
    
    def test_zero(self):
        obj = SafeObject(0)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == 0
    
    def test_empty_list(self):
        obj = SafeObject([])
        assert isinstance(obj, SafeObject)
        assert resolve(obj) == []
    
    def test_nested_safe_objects_with_parents(self):
        data = {"outer": {"inner": {"value": 42}}}
        obj = SafeObject(data)
        outer_obj = obj["outer"]
        inner_obj = outer_obj["inner"]
        value_obj = inner_obj["value"]
        
        assert parent(outer_obj) is obj
        assert parent(inner_obj) is outer_obj
        assert parent(value_obj) is inner_obj
    
    def test_complex_nested_structure(self):
        data = {
            "users": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ],
            "count": 2,
            "metadata": {
                "version": "1.0",
                "author": "test"
            }
        }
        obj = SafeObject(data)
        
        count = obj["count"]
        assert resolve(count) == 2
        
        users = obj["users"]
        first_user = users[0]
        first_name = first_user["name"]
        assert resolve(first_name) == "John"
        
        version = obj["metadata"]["version"]
        assert resolve(version) == "1.0"
    
    def test_dict_with_none_values(self):
        data = {"key": None}
        obj = SafeObject(data)
        result = obj["key"]
        assert isinstance(result, SafeObject)
        assert resolve(result) is None
    
    def test_accessing_method_on_dict(self):
        data = {"name": "John"}
        obj = SafeObject(data)
        # Accessing a dict method through SafeObject
        result = obj.get
        assert isinstance(result, SafeObject)
        # get is a method of dict, so it should exist
        assert resolve(result) is Unset  # But accessed as attribute, returns Unset


class TestSafeObjectTypeAnnotations:
    """Test type-related behavior."""
    
    def test_generic_type_preservation(self):
        data = {"key": "value"}
        obj: SafeObject[dict] = SafeObject(data)
        assert isinstance(obj, SafeObject)
    
    def test_resolve_overload_with_safe_object(self):
        obj = SafeObject(42)
        result = resolve(obj)
        assert result == 42
    
    def test_resolve_overload_with_non_safe_object(self):
        value = "hello"
        result = resolve(value)
        assert result == "hello"


class TestSafeObjectWithCallables:
    """Test SafeObject with callable objects."""
    
    def test_wrapping_function(self):
        def func():
            return "result"
        
        obj = SafeObject(func)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) is func
    
    def test_wrapping_lambda(self):
        lamb = lambda x: x * 2
        obj = SafeObject(lamb)
        assert isinstance(obj, SafeObject)
        assert resolve(obj) is lamb
    
    def test_wrapping_class_method(self):
        class MyClass:
            def method(self):
                return "result"
        
        instance = MyClass()
        obj = SafeObject(instance)
        method_obj = obj.method
        assert isinstance(method_obj, SafeObject)
        # The method should be accessible
        assert callable(resolve(method_obj))


class TestSafeObjectComparison:
    """Test comparison behavior through SafeObject."""
    
    def test_str_representation_equality(self):
        data1 = {"name": "John"}
        data2 = {"name": "John"}
        obj1 = SafeObject(data1)
        obj2 = SafeObject(data2)
        
        # String representations should be equal
        assert str(obj1) == str(obj2)
    
    def test_repr_representation_equality(self):
        data = {"name": "John"}
        obj1 = SafeObject(data)
        obj2 = SafeObject(data)
        
        # repr should show the wrapped value
        assert repr(obj1) == repr(obj2)