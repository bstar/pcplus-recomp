"""Observe an acknowledged online prefix before an intentional bridge stop.

This changes fault timing only. It neither forwards nor answers any bytes;
the final independent audit still requires complete upstream identity.
"""
import hashlib
import re
from modem import Telnet


def acknowledged_prefix(upstream, bbs_wire):
    upstream = bytes(upstream)
    if not upstream.endswith(b'\x06'):
        return None
    address, separator, body = upstream.partition(b'\r')
    if not separator or not re.fullmatch(rb'127\.0\.0\.1:\d+', address):
        return None
    received, _ = Telnet().feed(bytes(bbs_wire))
    if received != body:
        return None
    return dict(online_bytes=len(upstream), bbs_online_bytes=len(received),
                online_sha256=hashlib.sha256(upstream).hexdigest(),
                bbs_online_sha256=hashlib.sha256(received).hexdigest(),
                last_control_hex='06')
