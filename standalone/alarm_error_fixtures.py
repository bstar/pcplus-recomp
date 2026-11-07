"""Authored ALARM operand mutations, independent of original executables."""


def mutate(data, kind):
    if kind == 'negative':
        return data
    token = b'\x01\x01\xb5\x04'
    assert data.count(token) == 1
    at = data.index(token)
    if kind == 'option-truncated':
        return data[:at + 1]
    if kind == 'value-truncated':
        return data[:at + 3]
    assert kind in ('bad-tag', 'wide-negative')
    replacement = b'\x01\x01\xff\x00' if kind == 'bad-tag' else b'\x01\x01\xab\x00\x80'
    return data[:at] + replacement + data[at + 4:]
