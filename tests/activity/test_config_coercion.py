# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config._coercion import (
    coerce_bool,
    coerce_int,
    coerce_float,
)


class TestCoerceBool:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "Yes", "on", " on "])
    def test_truthy_strings(self, value):
        assert coerce_bool(value) is True

    @pytest.mark.parametrize("value", ["", "0", "false", "FALSE", "no", "off"])
    def test_falsy_strings(self, value):
        # Critically: bool("false") would be True; coerce_bool must return False.
        assert coerce_bool(value) is False

    def test_none_returns_default(self):
        assert coerce_bool(None) is False
        assert coerce_bool(None, default=True) is True

    def test_real_bools_passthrough(self):
        assert coerce_bool(True) is True
        assert coerce_bool(False) is False

    def test_numbers(self):
        assert coerce_bool(1) is True
        assert coerce_bool(0) is False

    def test_unrecognized_falls_back_to_default(self):
        assert coerce_bool("maybe") is False
        assert coerce_bool("maybe", default=True) is True


class TestCoerceInt:
    def test_none_returns_default(self):
        assert coerce_int(None, 3) == 3

    def test_empty_returns_default(self):
        assert coerce_int("", 3) == 3

    def test_int_passthrough(self):
        assert coerce_int(5, 3) == 5

    def test_numeric_string(self):
        assert coerce_int("5", 3) == 5

    def test_float_string_truncates(self):
        assert coerce_int("5.9", 3) == 5

    def test_bool_treated_as_unset(self):
        assert coerce_int(True, 3) == 3

    def test_invalid_raises_with_name(self):
        with pytest.raises(ValueError, match="RETRY_COUNT"):
            coerce_int("abc", 3, "RETRY_COUNT")


class TestCoerceFloat:
    def test_none_returns_default(self):
        assert coerce_float(None, 1.5) == 1.5

    def test_empty_returns_default(self):
        assert coerce_float("", 1.5) == 1.5

    def test_numeric_string(self):
        assert coerce_float("2.5", 1.5) == 2.5

    def test_int_passthrough(self):
        assert coerce_float(2, 1.5) == 2.0

    def test_bool_treated_as_unset(self):
        assert coerce_float(True, 1.5) == 1.5

    def test_invalid_raises_with_name(self):
        with pytest.raises(ValueError, match="REQUEST_TIMEOUT"):
            coerce_float("abc", 1.5, "REQUEST_TIMEOUT")
