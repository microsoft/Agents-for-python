# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity.config._coercion import (
    coerce_bool,
    coerce_int,
    coerce_float,
)


class TestCoerceBool:
    @pytest.mark.parametrize("value", ["1", "true", "TRUE", " true "])
    def test_truthy_strings(self, value):
        assert coerce_bool(value) is True

    @pytest.mark.parametrize("value", ["0", "false", "FALSE", " false "])
    def test_falsy_strings(self, value):
        # Critically: bool("false") would be True; coerce_bool must return False.
        assert coerce_bool(value) is False

    def test_none_unset_requires_default(self):
        # No default -> unset is an error, mirroring coerce_int/coerce_float.
        with pytest.raises(ValueError):
            coerce_bool(None)
        assert coerce_bool(None, default=True) is True
        assert coerce_bool(None, default=False) is False

    @pytest.mark.parametrize("value", ["", "   "])
    def test_empty_string_is_unset(self, value):
        # An empty/whitespace-only string is "unset", not an explicit False.
        with pytest.raises(ValueError):
            coerce_bool(value)
        assert coerce_bool(value, default=True) is True
        assert coerce_bool(value, default=False) is False

    def test_real_bools_passthrough(self):
        assert coerce_bool(True) is True
        assert coerce_bool(False) is False

    def test_numbers(self):
        assert coerce_bool(1) is True
        assert coerce_bool(0) is False

    @pytest.mark.parametrize("value", ["yes", "on", "no", "off"])
    def test_dropped_spellings_no_longer_parsed(self, value):
        # yes/on/no/off are intentionally not parsed; they are now unrecognized.
        with pytest.raises(ValueError):
            coerce_bool(value)
        assert coerce_bool(value, default=True) is True
        assert coerce_bool(value, default=False) is False

    def test_unrecognized_requires_default(self):
        with pytest.raises(ValueError):
            coerce_bool("maybe")
        assert coerce_bool("maybe", default=True) is True
        assert coerce_bool("maybe", default=False) is False


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
