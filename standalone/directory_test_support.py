"""Verify a successful call changes only the selected directory statistics."""
import datetime
import re
import struct


def accounting_check(before, after, entry, delta=1):
    if delta == 0:
        return before == after
    if len(before) != 23050 or len(after) != 23050 or not 1 <= entry <= 200:
        return False
    start = 250 + (entry - 1) * 114 + 61
    if before[:start] != after[:start] or before[start + 11:] != after[start + 11:]:
        return False
    date = after[start:start + 9]
    if not re.fullmatch(rb"[0-9]{2}/[0-9]{2}/[0-9]{2}\x00", date):
        return False
    month, day, year = map(int, date[:8].split(b"/"))
    try:
        datetime.date(2000 + year, month, day)
    except ValueError:
        return False
    old = struct.unpack_from('<H', before, start + 9)[0]
    new = struct.unpack_from('<H', after, start + 9)[0]
    return new == (old + delta) & 0xffff
