import pytest

from microsoft_agents.testing import Unset, DynamicObject
from microsoft_agents.testing.assertions.types.safe_object import resolve, parent


class TestDynamicObjectPrimitives:
    """Test DynamicObject with primitive types - should return primitives directly."""
    
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
    
    def test_zero_returns_zero(self):
        result = DynamicObject(0)
        assert result == 0
        assert isinstance(result, int)
        assert not isinstance(result, DynamicObject)
    
    def test_empty_string_returns_empty_string(self):
        result = DynamicObject("")
        assert result == ""
        assert isinstance(result, str)
        assert not isinstance(result, DynamicObject)


class TestDynamicObjectDict:
    """Test DynamicObject with dictionary values."""
    
    def test_dict_creates_dynamic_object(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert isinstance(obj, DynamicObject)
        assert resolve(obj) == data
    
    def test_getattr_on_dict(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        # DynamicObject returns primitives directly
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
        assert obj.user.profile.age == 30
    
    def test_empty_dict(self):
        obj = DynamicObject({})
        assert isinstance(obj, DynamicObject)
        assert resolve(obj) == {}


class TestDynamicObjectList:
    """Test DynamicObject with list values."""
    
    def test_list_creates_dynamic_object(self):
        data = [1, 2, 3]
        obj = DynamicObject(data)
        assert isinstance(obj, DynamicObject)
        assert resolve(obj) == data
    
    def test_getitem_on_list(self):
        data = ["a", "b", "c"]
        obj = DynamicObject(data)
        # List indexing returns wrapped items
        assert obj[0] == "a"
        assert obj[1] == "b"
        assert obj[2] == "c"
    
    def test_getitem_on_list_out_of_range(self):
        data = ["a", "b", "c"]
        obj = DynamicObject(data)
        with pytest.raises(IndexError):
            obj[10]
    
    def test_list_with_dicts(self):
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]
        obj = DynamicObject(data)
        assert obj[0]["name"] == "John"
        assert obj[1]["age"] == 25
    
    def test_list_with_nested_lists(self):
        data = [[1, 2], [3, 4], [5, 6]]
        obj = DynamicObject(data)
        assert obj[0][0] == 1
        assert obj[1][1] == 4
        assert obj[2][0] == 5
    
    def test_empty_list(self):
        obj = DynamicObject([])
        assert isinstance(obj, DynamicObject)
        assert resolve(obj) == []


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
        assert resolve(obj) is person
    
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
    
    def test_nested_custom_class(self):
        class Address:
            def __init__(self):
                self.street = "123 Main St"
                self.city = "Boston"
        
        class Person:
            def __init__(self):
                self.name = "John"
                self.address = Address()
        
        person = Person()
        obj = DynamicObject(person)
        assert obj.address.street == "123 Main St"
        assert obj.address.city == "Boston"


class TestDynamicObjectContains:
    """Test the __contains__ method."""
    
    def test_contains_with_dict(self):
        data = {"name": "John", "age": 30}
        obj = DynamicObject(data)
        assert "name" in obj
        assert "age" in obj
        assert "missing" not in obj
    
    def test_contains_with_list(self):
        data = [1, 2, 3, 4, 5]
        obj = DynamicObject(data)
        assert 1 in obj
        assert 3 in obj
        assert 10 not in obj
    
    def test_contains_with_string(self):
        # Strings are primitives and returned directly
        result = DynamicObject("hello")
        assert "h" in result
        assert "x" not in result
    
    def test_contains_with_set(self):
        data = {1, 2, 3, 4, 5}
        obj = DynamicObject(data)
        assert 1 in obj
        assert 10 not in obj
    
    def test_contains_with_tuple(self):
        data = (1, 2, 3)
        obj = DynamicObject(data)
        assert 1 in obj
        assert 10 not in obj
    
    def test_contains_with_non_iterable(self):
        data = 42
        obj = DynamicObject(data)
        # 42 is a primitive, returned directly, so this tests int
        with pytest.raises(TypeError):
            "test" in obj
    
    def test_contains_with_custom_class(self):
        class CustomContainer:
            def __contains__(self, item):
                return item == "special"
        
        obj = DynamicObject(CustomContainer())
        assert "special" in obj
        assert "other" not in obj


class TestDynamicObjectEquality:
    """Test the __eq__ method."""
    
    def test_equality_with_same_dict(self):
        data1 = {"name": "John"}
        data2 = {"name": "John"}
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        assert obj1 == obj2
    
    def test_equality_with_different_dict(self):
        data1 = {"name": "John"}
        data2 = {"name": "Jane"}
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        assert obj1 != obj2
    
    def test_equality_with_raw_value(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        assert obj == data
    
    def test_equality_with_primitives(self):
        # Primitives are returned as-is
        obj1 = DynamicObject(42)
        obj2 = DynamicObject(42)
        assert obj1 == obj2
        assert obj1 == 42
    
    def test_equality_with_list(self):
        data1 = [1, 2, 3]
        data2 = [1, 2, 3]
        obj1 = DynamicObject(data1)
        obj2 = DynamicObject(data2)
        assert obj1 == obj2
    
    def test_equality_with_custom_class(self):
        class Person:
            def __init__(self, name):
                self.name = name
            
            def __eq__(self, other):
                return isinstance(other, Person) and self.name == other.name
        
        person1 = Person("John")
        person2 = Person("John")
        obj1 = DynamicObject(person1)
        obj2 = DynamicObject(person2)
        assert obj1 == obj2


class TestDynamicObjectBool:
    """Test the __bool__ method."""
    
    def test_bool_with_non_empty_dict(self):
        obj = DynamicObject({"key": "value"})
        assert bool(obj) is True
    
    def test_bool_with_empty_dict(self):
        obj = DynamicObject({})
        assert bool(obj) is False
    
    def test_bool_with_non_empty_list(self):
        obj = DynamicObject([1, 2, 3])
        assert bool(obj) is True
    
    def test_bool_with_empty_list(self):
        obj = DynamicObject([])
        assert bool(obj) is False
    
    def test_bool_with_custom_class_true(self):
        class AlwaysTrue:
            def __bool__(self):
                return True
        
        obj = DynamicObject(AlwaysTrue())
        assert bool(obj) is True
    
    def test_bool_with_custom_class_false(self):
        class AlwaysFalse:
            def __bool__(self):
                return False
        
        obj = DynamicObject(AlwaysFalse())
        assert bool(obj) is False
    
    def test_bool_with_unset(self):
        # Unset is returned directly as primitive
        result = DynamicObject(Unset)
        assert bool(result) is False
    
    def test_bool_with_none(self):
        # None is returned directly as primitive
        result = DynamicObject(None)
        assert bool(result) is False


class TestDynamicObjectLen:
    """Test the __len__ method."""
    
    def test_len_with_dict(self):
        obj = DynamicObject({"a": 1, "b": 2, "c": 3})
        assert len(obj) == 3
    
    def test_len_with_list(self):
        obj = DynamicObject([1, 2, 3, 4, 5])
        assert len(obj) == 5
    
    def test_len_with_empty_dict(self):
        obj = DynamicObject({})
        assert len(obj) == 0
    
    def test_len_with_empty_list(self):
        obj = DynamicObject([])
        assert len(obj) == 0
    
    def test_len_with_string(self):
        # Strings are primitives, returned directly
        result = DynamicObject("hello")
        assert len(result) == 5
    
    def test_len_with_tuple(self):
        obj = DynamicObject((1, 2, 3))
        assert len(obj) == 3
    
    def test_len_with_set(self):
        obj = DynamicObject({1, 2, 3, 4})
        assert len(obj) == 4
    
    def test_len_with_non_sized_object(self):
        obj = DynamicObject(42)
        # 42 is primitive, returned directly
        with pytest.raises(TypeError):
            len(obj)
    
    def test_len_with_custom_class(self):
        class CustomSized:
            def __len__(self):
                return 42
        
        obj = DynamicObject(CustomSized())
        assert len(obj) == 42


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
    
    def test_deeply_nested_structure(self):
        data = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": "deep_value"
                        }
                    }
                }
            }
        }
        obj = DynamicObject(data)
        assert obj.a.b.c.d.e == "deep_value"


class TestDynamicObjectParent:
    """Test parent tracking."""
    
    def test_parent_is_none_for_root(self):
        obj = DynamicObject({"key": "value"})
        assert parent(obj) is None
    
    def test_parent_is_set_for_child(self):
        data = {"child": {"key": "value"}}
        obj = DynamicObject(data)
        child = obj["child"]
        assert isinstance(child, DynamicObject)
        assert parent(child) is obj
    
    def test_parent_chain(self):
        data = {"level1": {"level2": {"level3": "value"}}}
        obj = DynamicObject(data)
        level1 = obj["level1"]
        level2 = level1["level2"]
        assert parent(level2) is level1
        assert parent(level1) is obj


class TestDynamicObjectEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_nested_dynamic_objects(self):
        inner = {"value": 42}
        outer = {"inner": inner}
        obj = DynamicObject(outer)
        inner_obj = obj["inner"]
        assert isinstance(inner_obj, DynamicObject)
        assert resolve(inner_obj) == inner
    
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
        assert obj["users"][0]["name"] == "John"
        assert obj["users"][1]["age"] == 25
    
    def test_mixed_types_in_list(self):
        data = [1, "two", 3.0, True, None, {"key": "value"}]
        obj = DynamicObject(data)
        assert obj[0] == 1
        assert obj[1] == "two"
        assert obj[2] == 3.0
        assert obj[3] is True
        assert obj[4] is None
        assert obj[5]["key"] == "value"
    
    def test_wrapping_already_wrapped_object(self):
        data = {"key": "value"}
        obj1 = DynamicObject(data)
        obj2 = DynamicObject(obj1)
        # SafeObject.__new__ returns existing SafeObject
        assert obj2 is obj1
    
    def test_negative_list_indexing(self):
        data = [1, 2, 3, 4, 5]
        obj = DynamicObject(data)
        assert obj[-1] == 5
        assert obj[-2] == 4
    
    def test_slice_on_list(self):
        data = [1, 2, 3, 4, 5]
        obj = DynamicObject(data)
        sliced = obj[1:3]
        # Slicing returns a DynamicObject wrapping a list
        assert isinstance(sliced, DynamicObject)
        assert resolve(sliced) == [2, 3]


class TestDynamicObjectStringRepresentation:
    """Test string representations."""
    
    def test_str_with_dict(self):
        data = {"name": "John"}
        obj = DynamicObject(data)
        assert str(obj) == str(data)
    
    def test_str_with_list(self):
        data = [1, 2, 3]
        obj = DynamicObject(data)
        assert str(obj) == str(data)
    
    def test_str_with_custom_class(self):
        class Person:
            def __init__(self):
                self.name = "John"
            
            def __str__(self):
                return f"Person({self.name})"
        
        person = Person()
        obj = DynamicObject(person)
        assert str(obj) == "Person(John)"


class TestDynamicObjectWithParentParameter:
    """Test explicit parent parameter."""
    
    def test_with_explicit_parent(self):
        parent_data = {"parent": "value"}
        parent_obj = DynamicObject(parent_data)
        child_data = {"child": "value"}
        child_obj = DynamicObject(child_data, parent_obj)
        assert parent(child_obj) is parent_obj
    
    def test_with_none_parent(self):
        obj = DynamicObject({"key": "value"}, None)
        assert parent(obj) is None