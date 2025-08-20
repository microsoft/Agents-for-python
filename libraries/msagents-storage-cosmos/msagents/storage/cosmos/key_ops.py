from hashlib import sha256


def sanitize_key(
    key: str, key_suffix: str = "", compatibility_mode: bool = True
) -> str:
    """Return the sanitized key.

    Replace characters that are not allowed in keys in Cosmos.

    :param key: The provided key to be escaped.
    :param key_suffix: The string to add a the end of all RowKeys.
    :param compatibility_mode: True if keys should be truncated in order to support previous CosmosDb
        max key length of 255.  This behavior can be overridden by setting
        cosmosdb_config.compatibility_mode to False.
    :return str:
    """
    # forbidden characters
    bad_chars: list[str] = ["\\", "?", "/", "#", "\t", "\n", "\r", "*"]

    # replace those with with '*' and the
    # Unicode code point of the character and return the new string
    key = "".join(map(lambda x: "*" + str(ord(x)) if x in bad_chars else x, key))
    return truncate_key(f"{key}{key_suffix}", compatibility_mode)


def truncate_key(key: str, compatibility_mode: bool = True) -> str:
    """
    Truncate the key to 255 characters if compatibility_mode is True. If the key is longer than 255 characters,
    it will be truncated and a SHA-256 hash of the original key will be appended to minimize collisions.
    """
    max_key_len: int = 255

    if not compatibility_mode:
        return key

    if len(key) > max_key_len:
        # for now (and the foreseeable future), SHA-256 collisions are pretty infentesimally rare:
        # https://stackoverflow.com/questions/4014090/is-it-safe-to-ignore-the-possibility-of-sha-collisions-in-practice
        aux_hash = sha256(key.encode("utf-8"))
        aux_hex = aux_hash.hexdigest()

        key = key[0 : max_key_len - len(aux_hex)] + aux_hex

    return key
