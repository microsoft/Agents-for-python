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

    @pytest.fixture(params=["simple_value", {"key": "value"}, 42])
    def assertion_value(self, request):
        return request.param

    def test_parse_assertion_dict(self, assertion_value, assertion_type_str):

        assertion, assertion_type = _parse_assertion(
            {"assertion_type": assertion_type_str, "assertion": assertion_value}
        )
        assert assertion == assertion_value
        assert assertion_type.name == FieldAssertionType(assertion_type_str).name

    def test_parse_assertion_list(self, assertion_value, assertion_type_str):
        assertion, assertion_type = _parse_assertion(
            [assertion_type_str, assertion_value]
        )
        assert assertion == assertion_value
        assert assertion_type.name == assertion_type_str

    @pytest.mark.parametrize(
        "field",
        [
            "value",
            {"assertion_type": FieldAssertionType.IN},
            {"assertion_type": FieldAssertionType.IN, "key": "value"},
            [FieldAssertionType.RE_MATCH],
            [],
            {"assertion_type": "invalid", "assertion": "test"},
        ],
    )
    def test_parse_assertion_default(self, field):
        assertion, assertion_type = _parse_assertion(field)
        assert assertion == field
        assert assertion_type == FieldAssertionType.EQUALS
