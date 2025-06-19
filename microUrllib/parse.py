__all__ = [
    "quote",
    "quote_from_bytes",
    "unquote",
    "unquote_to_bytes",
]

# Characters valid in scheme names
scheme_chars = "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "+-."

# XXX: Consider replacing with functools.lru_cache
MAX_CACHE_SIZE = 20

_ALWAYS_SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ" b"abcdefghijklmnopqrstuvwxyz" b"0123456789" b"_.-")
_ALWAYS_SAFE_BYTES = bytes(_ALWAYS_SAFE)
_safe_quoters = {}


def clear_cache():
    """Clear the parse cache and the quoters cache."""
    _safe_quoters.clear()


_hexdig = "0123456789ABCDEFabcdef"
_hextobyte = {(a + b).encode(): bytes([int(a + b, 16)]) for a in _hexdig for b in _hexdig}


def unquote_to_bytes(string):
    """unquote_to_bytes('abc%20def') -> b'abc def'."""
    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        # Is it a string-like object?
        string.split
        return b""
    if isinstance(string, str):
        string = string.encode("utf-8")
    bits = string.split(b"%")
    if len(bits) == 1:
        return string
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            append(_hextobyte[item[:2]])
            append(item[2:])
        except KeyError:
            append(b"%")
            append(item)
    return b"".join(res)


def split_on_non_ascii(s):
    """
    Splits the input string wherever a character is not ASCII (ord(c) not in 0..127).
    Returns a list of substrings and the non-ASCII characters as separate elements.
    """
    result = []
    current = []
    for c in s:
        if 0 <= ord(c) <= 127:
            current.append(c)
        else:
            if current:
                result.append("".join(current))
                current = []
            result.append(c)
    if current:
        result.append("".join(current))
    return result


def unquote(string, encoding="utf-8", errors="replace"):
    """Replace %xx escapes by their single-character equivalent. The optional
    encoding and errors parameters specify how to decode percent-encoded
    sequences into Unicode characters, as accepted by the bytes.decode()
    method.
    By default, percent-encoded sequences are decoded with UTF-8, and invalid
    sequences are replaced by a placeholder character.

    unquote('abc%20def') -> 'abc def'.
    """
    if "%" not in string:
        string.split
        return string
    if encoding is None:
        encoding = "utf-8"
    if errors is None:
        errors = "replace"
    bits = split_on_non_ascii(string)
    res = []
    append = res.append
    for i in range(0, len(bits), 2):
        append(unquote_to_bytes(bits[i]).decode(encoding, errors))
        if i + 1 < len(bits):
            # Append the non-ASCII part as is
            append(bits[i + 1])
    return "".join(res)


class Quoter:
    """A mapping from bytes (in range(0,256)) to strings.

    String values are percent-encoded byte values, unless the key < 128, and
    in the "safe" set (either the specified safe set, or default set).
    """

    # Keeps a cache internally, using defaultdict, for efficiency (lookups
    # of cached keys don't call Python code at all).
    def __init__(self, safe):
        """safe: bytes object."""
        self.safe = _ALWAYS_SAFE.union(safe)
        self.cache = {}

    def get(self, b):
        try:
            return self.cache[b]
        except KeyError:
            # Handle a cache miss. Store quoted string in cache and return.
            res = chr(b) if b in self.safe else "%{:02X}".format(b)
            self.cache[b] = res
            return res


def quote(string, safe="/", encoding=None, errors=None):
    """quote('abc def') -> 'abc%20def'

    Each part of a URL, e.g. the path info, the query, etc., has a
    different set of reserved characters that must be quoted.

    RFC 2396 Uniform Resource Identifiers (URI): Generic Syntax lists
    the following reserved characters.

    reserved    = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
                  "$" | ","

    Each of these characters is reserved in some component of a URL,
    but not necessarily in all of them.

    By default, the quote function is intended for quoting the path
    section of a URL.  Thus, it will not encode '/'.  This character
    is reserved, but in typical usage the quote function is being
    called on a path where the existing slash characters are used as
    reserved characters.

    string and safe may be either str or bytes objects. encoding must
    not be specified if string is a str.

    The optional encoding and errors parameters specify how to deal with
    non-ASCII characters, as accepted by the str.encode method.
    By default, encoding='utf-8' (characters are encoded with UTF-8), and
    errors='strict' (unsupported characters raise a UnicodeEncodeError).
    """
    if isinstance(string, str):
        if not string:
            return string
        if encoding is None:
            encoding = "utf-8"
        if errors is None:
            errors = "strict"
        string = string.encode(encoding, errors)
    else:
        if encoding is not None:
            raise TypeError("quote() doesn't support 'encoding' for bytes")
        if errors is not None:
            raise TypeError("quote() doesn't support 'errors' for bytes")
    return quote_from_bytes(string, safe)


def quote_from_bytes(bs, safe="/"):
    """Like quote(), but accepts a bytes object rather than a str, and does
    not perform string-to-bytes encoding.  It always returns an ASCII string.
    quote_from_bytes(b'abc def\x3f') -> 'abc%20def%3f'
    """
    if not isinstance(bs, (bytes, bytearray)):
        raise TypeError("quote_from_bytes() expected bytes")
    if not bs:
        return ""
    if isinstance(safe, str):
        # Normalize 'safe' by converting to bytes and removing non-ASCII chars
        safe = safe.encode("ascii", "ignore")
    else:
        safe = bytes([c for c in safe if c < 128])
    if not bs.rstrip(_ALWAYS_SAFE_BYTES + safe):
        return bs.decode()
    try:
        quoter = _safe_quoters[safe]
    except KeyError as e:
        _safe_quoters[safe] = quoter = Quoter(safe)

    res = ""
    for char in bs:
        res += quoter.get(char)
    return res
