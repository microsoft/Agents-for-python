import pytest

from microsoft_agents.testing.assertions.type_defs import FieldAssertionType
from microsoft_agents.testing.assertions.check_activity import _parse_assertion

class TestParseAssertion:

    @pytest.fixture(
        params=[
            FieldAssertionType.EQUALS.value,
            FieldAssertionType.NOT_EQUALS.value,
            FieldAssertionType.GREATER_THAN.value,
        ]
    )
    def assertion_type_str(self, request):
        return request.param

    @pytest.fixture(
        params=[
            "simple_value",
            {"key": "value"},
            42
        ]
    )
    def assertion_value(self, request):
        return request.param
    
    def test_parse_assertion_dict(self, assertion_value, assertion_type_str):
        
        assertion, assertion_type = _parse_assertion(
            {"assertion_type": assertion_type_str, "assertion": assertion_value}
        )
        assert assertion == assertion_value
        assert assertion_type.name ==  FieldAssertionType(assertion_type_str).name

    def test_parse_assertion_dict_complex():
        
        assertion, assertion_type = _parse_assertion(
            {"assertion_type": "__EQ__", "assertion": {"key": "value"}}
        )

        assert assertion == {"key": "value"}
        assert assertion_type.name == "__EQ__"

    def test_parse_assertion_dict_no_value():
        
        assertion, assertion_type = _parse_assertion(
            {"assertion_type": "__NEQ__"}
        )

        assert assertion is None
        assert assertion_type.name == "__NEQ__"

    def test_parse_assertion_dict_extra_value():
        
        assertion, assertion_type = _parse_assertion(
            {"assertion_type": "__RE_MATCH__", "key": "value"}
        )

        assert assertion is None
        assert assertion_type.name == "__RE_MATCH__"

    def test_parse_assertion_list():
        
        assertion, assertion_type = _parse_assertion(
            ["__GT__", 10]
        )

        assert assertion == 10
        assert assertion_type.name == "__GT__"