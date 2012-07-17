#sdobrev 2010
'py2 version of py3 urllib.parse.unquote'

def unquote(string, encoding='utf-8', errors='replace'):
    """Replace %xx escapes by their single-character equivalent. The optional
    encoding and errors parameters specify how to decode percent-encoded
    sequences into Unicode characters, as accepted by the bytes.decode()
    method.
    By default, percent-encoded sequences are decoded with UTF-8, and invalid
    sequences are replaced by a placeholder character.

    unquote('abc%20def') -> 'abc def'.
    """
    if string == '':
        return string
    res = string.split('%')
    if len(res) == 1:
        return string
    if encoding is None:
        encoding = 'utf-8'
    if errors is None:
        errors = 'replace'
    # pct_sequence: contiguous sequence of percent-encoded bytes, decoded
    pct_sequence = b''
    string = res[0]
    for item in res[1:]:
        try:
            if not item:
                raise ValueError
            pct_sequence += chr( int( item[:2], 16))
            rest = item[2:]
            if not rest:
                # This segment was just a single percent-encoded character.
                # May be part of a sequence of code units, so delay decoding.
                # (Stored in pct_sequence).
                continue
        except ValueError:
            rest = '%' + item
        # Encountered non-percent-encoded characters. Flush the current
        # pct_sequence.
        string += pct_sequence.decode(encoding, errors) + rest
        pct_sequence = b''
    if pct_sequence:
        # Flush the final pct_sequence
        string += pct_sequence.decode(encoding, errors)
    return string

# vim:ts=4:sw=4:expandtab
