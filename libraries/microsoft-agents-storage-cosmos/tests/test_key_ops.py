import hashlib
import pytest
from microsoft.agents.storage.cosmos.key_ops import truncate_key, sanitize_key

# thank you AI


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("validKey123", "validKey123"),
        ("simple", "simple"),
        ("CamelCase", "CamelCase"),
        ("under_score", "under_score"),
        ("with-dash", "with-dash"),
        ("with.dot", "with.dot"),
    ],
)
def test_sanitize_key_simple(input_key, expected):
    assert sanitize_key(input_key) == expected


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("key\\value", "key*92value"),
        ("key?value", "key*63value"),
        ("key/value", "key*47value"),
        ("key#value", "key*35value"),
        ("key\tvalue", "key*9value"),
        ("key\nvalue", "key*10value"),
        ("key\rvalue", "key*13value"),
        ("key*value", "key*42value"),
    ],
)
def test_sanitize_key_forbidden_chars(input_key, expected):
    assert sanitize_key(input_key) == expected


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("key/with\\many?bad#chars", "key*47with*92many*63bad*35chars"),
        ("a\\b/c?d#e\tf\ng\rh*i", "a*92b*47c*63d*35e*9f*10g*13h*42i"),
        ("key/with\\many?bad#chars", "key*47with*92many*63bad*35chars"),
    ],
)
def test_sanitize_key_multiple_forbidden_chars(input_key, expected):
    assert sanitize_key(input_key) == expected


def test_sanitize_key_with_long_key_with_forbidden_chars():
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key)
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "\t" not in sanitized


def test_sanitize_key_with_long_key_with_forbidden_chars_with_suffix():
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key, key_suffix="_suff?#*")
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "#" not in sanitized


def test_sanitize_key_with_long_key_with_forbidden_chars_with_suffix_compat_mode():
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key, key_suffix="_suff?#*", compatibility_mode=True)
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "#" not in sanitized


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("", ""),
        ("   ", "   "),
    ],
)
def test_sanitize_key_empty_and_whitespace(input_key, expected):
    assert sanitize_key(input_key) == expected


@pytest.mark.parametrize(
    "input_key,suffix,expected",
    [
        ("key", "_suffix", "key_suffix"),
        ("test", "123", "test123"),
        ("key/value", "_clean", "key*47value_clean"),
        ("", "_suffix", "_suffix"),
    ],
)
def test_sanitize_key_with_suffix(input_key, suffix, expected):
    assert sanitize_key(input_key, key_suffix=suffix) == expected


def test_sanitize_key_suffix_with_truncation():
    long_key = "a" * 250
    suffix = "_suffix"
    result = sanitize_key(long_key, key_suffix=suffix, compatibility_mode=True)
    assert len(result) <= 255
    assert (
        result.endswith(suffix) or len(result) == 255
    )  # Either has suffix or was truncated


def test_sanitize_key_truncation_compatibility_mode():
    long_key = "a" * 300
    result = sanitize_key(long_key, compatibility_mode=True)
    assert len(result) <= 255

    # Should contain hash when truncated
    very_long_key = "b" * 500
    result2 = sanitize_key(very_long_key, compatibility_mode=True)
    assert len(result2) == 255


def test_sanitize_key_no_truncation():
    long_key = "a" * 300
    result = sanitize_key(long_key, compatibility_mode=False)
    assert result == long_key  # Should be unchanged
    assert len(result) == 300


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("short", "short"),
        ("a" * 254, "a" * 254),
        ("a" * 255, "a" * 255),
    ],
)
def test_truncate_key_short_strings(input_key, expected):
    assert truncate_key(input_key) == expected


def test_truncate_key_long_strings():
    long_key = "a" * 300
    result = truncate_key(long_key)
    assert len(result) == 255

    # Result should end with SHA256 hash
    expected_hash = hashlib.sha256(long_key.encode("utf-8")).hexdigest()
    assert result.endswith(expected_hash)

    # First part should be original key truncated
    expected_prefix_len = 255 - len(expected_hash)
    assert result.startswith("a" * expected_prefix_len)


@pytest.mark.parametrize(
    "input_key,compatibility_mode,expected_unchanged",
    [
        ("a" * 300, False, True),  # Should be unchanged
        ("x" * 1000, False, True),  # Should be unchanged
        (
            "key/with\\special?chars#and\ttabs\nand\rmore*",
            False,
            True,
        ),  # Should be unchanged
    ],
)
def test_truncate_key_compatibility_mode_disabled(
    input_key, compatibility_mode, expected_unchanged
):
    result = truncate_key(input_key, compatibility_mode=compatibility_mode)
    if expected_unchanged:
        assert result == input_key


@pytest.mark.parametrize(
    "input_key,expected_length",
    [
        ("a" * 255, 255),
        ("a" * 256, 255),
    ],
)
def test_truncate_key_exact_and_over_limit(input_key, expected_length):
    result = truncate_key(input_key)
    assert len(result) == expected_length

    if len(input_key) == 255:
        assert result == input_key
    else:
        assert result != input_key


def test_truncate_key_hash_consistency():
    long_key = "consistent_test_key_" * 20  # > 255 chars
    result1 = truncate_key(long_key)
    result2 = truncate_key(long_key)
    assert result1 == result2
    assert len(result1) == 255


@pytest.mark.parametrize(
    "key1,key2",
    [
        ("a" * 300, "b" * 300),
        ("consistent_test_key_" * 20, "different_test_key_" * 20),
    ],
)
def test_truncate_key_different_inputs_different_outputs(key1, key2):
    result1 = truncate_key(key1)
    result2 = truncate_key(key2)
    assert result1 != result2
    assert len(result1) == len(result2) == 255


def test_sanitize_key_integration():
    # Key with forbidden chars that will be long after sanitization + suffix
    base_key = "test/key\\with?many#forbidden\tchars\nand\rmore*" * 10
    suffix = "_integration_test"

    result = sanitize_key(base_key, key_suffix=suffix, compatibility_mode=True)

    # Should be sanitized and truncated
    assert len(result) <= 255
    assert "*47" in result or "*92" in result  # Contains sanitized chars

    # Test without truncation
    result_no_trunc = sanitize_key(
        base_key, key_suffix=suffix, compatibility_mode=False
    )
    assert (
        "*47" in result_no_trunc or "*92" in result_no_trunc
    )  # Contains sanitized chars
    assert result_no_trunc.endswith(suffix)


@pytest.mark.parametrize(
    "input_key,expected",
    [
        ("key_ñ_测试", "key_ñ_测试"),
        ("123456789", "123456789"),
        ("MyKey/WithSlash", "MyKey*47WithSlash"),
    ],
)
def test_edge_cases(input_key, expected):
    result = sanitize_key(input_key)
    assert result == expected
