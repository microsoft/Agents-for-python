import hashlib

from microsoft.agents.cosmos.key_ops import truncate_key, sanitize_key

# thank you AI


def test_sanitize_key_simple():
    """Test sanitize_key with valid keys that shouldn't change"""
    assert sanitize_key("validKey123") == "validKey123"
    assert sanitize_key("simple") == "simple"
    assert sanitize_key("CamelCase") == "CamelCase"
    assert sanitize_key("under_score") == "under_score"
    assert sanitize_key("with-dash") == "with-dash"
    assert sanitize_key("with.dot") == "with.dot"


def test_sanitize_key_forbidden_chars():
    """Test sanitize_key with forbidden characters"""
    # Test each forbidden character individually
    assert sanitize_key("key\\value") == "key*92value"  # backslash
    assert sanitize_key("key?value") == "key*63value"  # question mark
    assert sanitize_key("key/value") == "key*47value"  # forward slash
    assert sanitize_key("key#value") == "key*35value"  # hash
    assert sanitize_key("key\tvalue") == "key*9value"  # tab
    assert sanitize_key("key\nvalue") == "key*10value"  # newline
    assert sanitize_key("key\rvalue") == "key*13value"  # carriage return
    assert sanitize_key("key*value") == "key*42value"  # asterisk


def test_sanitize_key_multiple_forbidden_chars():
    """Test sanitize_key with multiple forbidden characters"""
    assert sanitize_key("key/with\\many?bad#chars") == "key*47with*92many*63bad*35chars"
    assert sanitize_key("a\\b/c?d#e\tf\ng\rh*i") == "a*92b*47c*63d*35e*9f*10g*13h*42i"


def test_sanitize_key_with_long_key_with_forbidden_chars():
    """Test sanitize_key with a long key that requires truncation"""
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key)
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "\t" not in sanitized


def test_sanitize_key_with_long_key_with_forbidden_chars_with_suffix():
    """Test sanitize_key with a long key that requires truncation"""
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key, key_suffix="_suff?#*")
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "#" not in sanitized


def test_sanitize_key_with_long_key_with_forbidden_chars_with_suffix_compat_mode():
    """Test sanitize_key with a long key that requires truncation"""
    long_key = "a?2/!@\t3." * 100  # Create a long key
    sanitized = sanitize_key(long_key, key_suffix="_suff?#*", compatibility_mode=True)
    assert len(sanitized) <= 255  # Should be truncated
    # Ensure forbidden characters are replaced
    assert "?" not in sanitized
    assert "/" not in sanitized
    assert "#" not in sanitized


def test_sanitize_key_empty_and_whitespace():
    """Test sanitize_key with empty and whitespace strings"""
    assert sanitize_key("") == ""
    assert sanitize_key("   ") == "   "  # spaces are allowed
    assert sanitize_key(" key ") == " key "  # leading/trailing spaces preserved


def test_sanitize_key_with_suffix():
    """Test sanitize_key with key_suffix parameter"""
    assert sanitize_key("key", key_suffix="_suffix") == "key_suffix"
    assert sanitize_key("test", key_suffix="123") == "test123"
    assert sanitize_key("key/value", key_suffix="_clean") == "key*47value_clean"
    assert sanitize_key("", key_suffix="_suffix") == "_suffix"


def test_sanitize_key_suffix_with_truncation():
    """Test sanitize_key with suffix that causes truncation"""
    long_key = "a" * 250
    suffix = "_suffix"
    result = sanitize_key(long_key, key_suffix=suffix, compatibility_mode=True)
    assert len(result) <= 255
    assert (
        result.endswith(suffix) or len(result) == 255
    )  # Either has suffix or was truncated


def test_sanitize_key_truncation_compatibility_mode():
    """Test sanitize_key with truncation in compatibility mode"""
    long_key = "a" * 300
    result = sanitize_key(long_key, compatibility_mode=True)
    assert len(result) <= 255

    # Should contain hash when truncated
    very_long_key = "b" * 500
    result2 = sanitize_key(very_long_key, compatibility_mode=True)
    assert len(result2) == 255


def test_sanitize_key_no_truncation():
    """Test sanitize_key without compatibility mode (no truncation)"""
    long_key = "a" * 300
    result = sanitize_key(long_key, compatibility_mode=False)
    assert result == long_key  # Should be unchanged
    assert len(result) == 300


def test_truncate_key_short_strings():
    """Test truncate_key with strings shorter than 255 characters"""
    assert truncate_key("short") == "short"
    assert truncate_key("a" * 254) == "a" * 254
    assert truncate_key("a" * 255) == "a" * 255


def test_truncate_key_long_strings():
    """Test truncate_key with strings longer than 255 characters"""
    long_key = "a" * 300
    result = truncate_key(long_key)
    assert len(result) == 255

    # Result should end with SHA256 hash
    expected_hash = hashlib.sha256(long_key.encode("utf-8")).hexdigest()
    assert result.endswith(expected_hash)

    # First part should be original key truncated
    expected_prefix_len = 255 - len(expected_hash)
    assert result.startswith("a" * expected_prefix_len)


def test_truncate_key_compatibility_mode_disabled():
    """Test truncate_key with compatibility_mode=False"""
    long_key = "a" * 300
    assert truncate_key(long_key, compatibility_mode=False) == long_key

    very_long_key = "x" * 1000
    assert truncate_key(very_long_key, compatibility_mode=False) == very_long_key

    # Should work with any characters when compatibility mode is off
    special_chars = "key/with\\special?chars#and\ttabs\nand\rmore*"
    assert truncate_key(special_chars, compatibility_mode=False) == special_chars


def test_truncate_key_exactly_255_chars():
    """Test truncate_key with exactly 255 characters"""
    key_255 = "a" * 255
    assert truncate_key(key_255) == key_255
    assert len(truncate_key(key_255)) == 255


def test_truncate_key_256_chars():
    """Test truncate_key with 256 characters (one over limit)"""
    key_256 = "a" * 256
    result = truncate_key(key_256)
    assert len(result) == 255
    assert result != key_256


def test_truncate_key_hash_consistency():
    """Test that truncate_key produces consistent hashes for same input"""
    long_key = "consistent_test_key_" * 20  # > 255 chars
    result1 = truncate_key(long_key)
    result2 = truncate_key(long_key)
    assert result1 == result2
    assert len(result1) == 255


def test_truncate_key_different_inputs_different_outputs():
    """Test that different long keys produce different truncated results"""
    key1 = "a" * 300
    key2 = "b" * 300
    result1 = truncate_key(key1)
    result2 = truncate_key(key2)
    assert result1 != result2
    assert len(result1) == len(result2) == 255


def test_sanitize_key_integration():
    """Integration test combining forbidden chars, suffix, and truncation"""
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


def test_edge_cases():
    """Test various edge cases"""
    # Unicode characters (should be preserved)
    assert sanitize_key("key_ñ_测试") == "key_ñ_测试"

    # Numbers only
    assert sanitize_key("123456789") == "123456789"

    # Mixed case with special chars
    result = sanitize_key("MyKey/WithSlash")
    assert result == "MyKey*47WithSlash"

    # Key that becomes exactly 255 chars after sanitization
    # Create a key that will be exactly 255 after replacing one char
    base = "a" * 252 + "/"  # 253 chars, "/" becomes "*47" (3 chars) = 255 total
    result = sanitize_key(base)
    assert len(result) == 255
    assert result.endswith("*47")
