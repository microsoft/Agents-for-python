# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.testing.assertions.dynamic_object import DynamicObject
from microsoft_agents.testing.assertions.unset import Unset


class TestDynamicObject:

    def test_init_with_simple_value(self):
        """Test DynamicObject initialization with a simple value."""
        obj = DynamicObject(42)
        assert obj._value == 42

    def test_init_with_string(self):
        """Test DynamicObject initialization with a string."""
        obj = DynamicObject("hello")
        assert obj._value == "hello"

    def test_init_with_dict(self):
        """Test DynamicObject initialization with a dictionary."""
        data = {"key": "value"}
        obj = DynamicObject(data)
        assert obj._value == data

    def test_init_with_object(self):
        """Test DynamicObject initialization with a custom object."""
        class CustomObject:
            def __init__(self):
                self.name = "test"
                self.value = 123
        
        custom = CustomObject()
        obj = DynamicObject(custom)
        assert obj._value == custom

    def test_getattribute_returns_primitive_int(self):
        """Test that getattribute returns primitive int directly."""
        class TestObj:
            number = 42
        
        obj = DynamicObject(TestObj())
        result = obj.number
        assert result == 42
        assert isinstance(result, int)

    def test_getattribute_returns_primitive_float(self):
        """Test that getattribute returns primitive float directly."""
        class TestObj:
            pi = 3.14
        
        obj = DynamicObject(TestObj())
        result = obj.pi
        assert result == 3.14
        assert isinstance(result, float)

    def test_getattribute_returns_primitive_string(self):
        """Test that getattribute returns primitive string directly."""
        class TestObj:
            name = "test"
        
        obj = DynamicObject(TestObj())
        result = obj.name
        assert result == "test"
        assert isinstance(result, str)

    def test_getattribute_returns_primitive_bool(self):
        """Test that getattribute returns primitive bool directly."""
        class TestObj:
            flag = True
        
        obj = DynamicObject(TestObj())
        result = obj.flag
        assert result is True
        assert isinstance(result, bool)

    def test_getattribute_wraps_complex_object(self):
        """Test that getattribute wraps non-primitive attributes in DynamicObject."""
        class Inner:
            value = "inner"
        
        class Outer:
            inner = Inner()
        
        obj = DynamicObject(Outer())
        result = obj.inner
        assert isinstance(result, DynamicObject)
        assert result._value.value == "inner"

    def test_getattribute_chain(self):
        """Test chaining attribute access through multiple DynamicObjects."""
        class Level3:
            data = "deep"
        
        class Level2:
            level3 = Level3()
        
        class Level1:
            level2 = Level2()
        
        obj = DynamicObject(Level1())
        result = obj.level2.level3.data
        assert result == "deep"

    def test_getattribute_missing_attribute_returns_unset(self):
        """Test that accessing a missing attribute returns Unset."""
        class TestObj:
            existing = "value"
        
        obj = DynamicObject(TestObj())
        result = obj.nonexistent
        assert result._value == Unset

    def test_value_method_returns_wrapped_value(self):
        """Test that value() method returns the original wrapped value."""
        data = {"key": "value"}
        obj = DynamicObject(data)
        assert obj.value() == data
        assert obj.value() is data

    def test_value_method_with_custom_object(self):
        """Test value() method with custom object."""
        class CustomObject:
            name = "test"
        
        custom = CustomObject()
        obj = DynamicObject(custom)
        assert obj.value() is custom

    def test_equality_with_another_dynamic_object(self):
        """Test equality comparison between two DynamicObjects."""
        obj1 = DynamicObject(42)
        obj2 = DynamicObject(42)
        assert obj1 == obj2

    def test_equality_with_another_dynamic_object_different_values(self):
        """Test inequality between DynamicObjects with different values."""
        obj1 = DynamicObject(42)
        obj2 = DynamicObject(43)
        assert not (obj1 == obj2)

    def test_equality_with_direct_value(self):
        """Test equality comparison with direct value."""
        obj = DynamicObject(42)
        assert obj == 42

    def test_equality_with_string(self):
        """Test equality comparison with string value."""
        obj = DynamicObject("hello")
        assert obj == "hello"

    def test_equality_with_dict(self):
        """Test equality comparison with dictionary."""
        data = {"key": "value"}
        obj = DynamicObject(data)
        assert obj == data

    def test_equality_with_list(self):
        """Test equality comparison with list."""
        data = [1, 2, 3]
        obj = DynamicObject(data)
        assert obj == data

    def test_in_operator_with_dynamic_object(self):
        """Test __in__ method with another DynamicObject."""
        obj1 = DynamicObject(5)
        obj2 = DynamicObject([1, 2, 3, 4, 5])
        result = obj1.__in__(obj2)
        assert result is True

    def test_in_operator_with_direct_collection(self):
        """Test __in__ method with direct collection."""
        obj = DynamicObject(5)
        result = obj.__in__([1, 2, 3, 4, 5])
        assert result is True

    def test_in_operator_not_in_collection(self):
        """Test __in__ method when value is not in collection."""
        obj = DynamicObject(10)
        result = obj.__in__([1, 2, 3, 4, 5])
        assert result is False

    def test_in_operator_with_string(self):
        """Test __in__ method with string containment."""
        obj = DynamicObject("lo")
        result = obj.__in__("hello")
        assert result is True

    def test_str_method_with_int(self):
        """Test __str__ method with integer value."""
        obj = DynamicObject(42)
        assert str(obj) == "42"

    def test_str_method_with_string(self):
        """Test __str__ method with string value."""
        obj = DynamicObject("hello")
        assert str(obj) == "hello"

    def test_str_method_with_dict(self):
        """Test __str__ method with dictionary value."""
        data = {"key": "value"}
        obj = DynamicObject(data)
        assert str(obj) == str(data)

    def test_repr_method(self):
        """Test __repr__ method returns proper representation."""
        obj = DynamicObject(42)
        assert repr(obj) == "DynamicObject(42)"

    def test_repr_method_with_string(self):
        """Test __repr__ method with string value."""
        obj = DynamicObject("hello")
        assert repr(obj) == "DynamicObject('hello')"

    def test_repr_method_with_dict(self):
        """Test __repr__ method with dictionary value."""
        data = {"key": "value"}
        obj = DynamicObject(data)
        assert repr(obj) == f"DynamicObject({data!r})"

    def test_wrapped_object_method_access(self):
        """Test accessing methods through DynamicObject."""
        class TestObj:
            def get_value(self):
                return "method_result"
        
        obj = DynamicObject(TestObj())
        method = obj.get_value
        # Method should be wrapped in DynamicObject
        assert isinstance(method, DynamicObject)

    def test_nested_dict_access(self):
        """Test accessing nested dictionary values."""
        class TestObj:
            data = {"nested": {"value": 42}}
        
        obj = DynamicObject(TestObj())
        result = obj.data
        # Dictionary should be wrapped in DynamicObject
        assert isinstance(result, DynamicObject)
        assert result.value() == {"nested": {"value": 42}}

    def test_list_attribute_wrapping(self):
        """Test that list attributes are wrapped in DynamicObject."""
        class TestObj:
            items = [1, 2, 3]
        
        obj = DynamicObject(TestObj())
        result = obj.items
        assert isinstance(result, DynamicObject)
        assert result.value() == [1, 2, 3]

    def test_none_value_handling(self):
        """Test handling of None value."""
        obj = DynamicObject(None)
        assert obj._value is None
        assert obj.value() is None
        assert str(obj) == "None"

    def test_equality_with_none(self):
        """Test equality comparison with None."""
        obj = DynamicObject(None)
        assert obj == None

    def test_zero_value_handling(self):
        """Test handling of zero as a primitive."""
        class TestObj:
            count = 0
        
        obj = DynamicObject(TestObj())
        result = obj.count
        assert result == 0
        assert isinstance(result, int)

    def test_empty_string_handling(self):
        """Test handling of empty string as a primitive."""
        class TestObj:
            text = ""
        
        obj = DynamicObject(TestObj())
        result = obj.text
        assert result == ""
        assert isinstance(result, str)

    def test_false_boolean_handling(self):
        """Test handling of False as a primitive."""
        class TestObj:
            flag = False
        
        obj = DynamicObject(TestObj())
        result = obj.flag
        assert result is False
        assert isinstance(result, bool)