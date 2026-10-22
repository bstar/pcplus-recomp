#!/usr/bin/env python3
"""Bounded source-recorder core with modeled checked stream callbacks.

Host C execution and generated-source compiler checks only. No terminal/UI,
DOS filesystem, UART or complete compiler/VM replay is accepted here.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source
U = C.c_uint
P = C.c_void_p
WRITE = C.CFUNCTYPE(U, P, P, U, P)
CLOSE = C.CFUNCTYPE(U, P)


class Ops(C.Structure):
    _fields_ = [('write', WRITE), ('close', CLOSE)]


class Session(C.Structure):
    _fields_ = [('ops', Ops), ('context', P)] + [(name, U) for name in
        ('started', 'active', 'owned', 'busy', 'status', 'write_error', 'close_error',
         'tx_count', 'rx_count', 'timeout')] + [('tx', C.c_ubyte * 40), ('rx', C.c_ubyte * 16)] + [
         (name, C.c_ulong) for name in ('transmitted_bytes', 'received_bytes', 'source_bytes')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    inputs = [Path(__file__).resolve(), ROOT / 'src/aspect/recorder.c',
              ROOT / 'src/aspect/recorder.h', ROOT / 'src/aspect/compiler.py']
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    for path in inputs:
        copy = out / 'frozen-source' / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(path.read_bytes())
    subprocess.run(['gcc', '-std=c89', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    str(ROOT / 'src/aspect/recorder.c'), '-o', str(out / 'recorder.so')], check=True)
    lib = C.CDLL(str(out / 'recorder.so'))
    lib.aspect_recorder_start.argtypes = [P, P, P, U]
    for name in ('transmit', 'receive'):
        getattr(lib, 'aspect_recorder_' + name).argtypes = [P, P, U]
    for name in ('flush', 'stop', 'cancel'):
        getattr(lib, 'aspect_recorder_' + name).argtypes = [P]
    cases = []

    class Sink:
        def __init__(self, short=65535, fail=0, close=0, zero=False, excess=False, reenter=False):
            self.session = Session()
            self.data = bytearray()
            self.writes = self.closes = 0
            self.fail = fail
            self.close_error = close
            self.short = short
            self.zero = zero
            self.excess = excess
            self.reenter = reenter
            self.reentered = []
            self.write_cb = WRITE(self.write)
            self.close_cb = CLOSE(self.close)
            self.ops = Ops(self.write_cb, self.close_cb)

        def write(self, context, pointer, count, result):
            self.writes += 1
            if self.reenter:
                self.reentered.append(lib.aspect_recorder_stop(C.byref(self.session)))
            actual = 0 if self.zero or self.fail else min(count, self.short)
            C.cast(result, C.POINTER(U))[0] = count + 1 if self.excess else actual
            self.data.extend(C.string_at(pointer, actual))
            return self.fail

        def close(self, context):
            self.closes += 1
            return self.close_error

        def call(self, name, data=None):
            fn = getattr(lib, 'aspect_recorder_' + name)
            if name == 'start':
                return fn(C.byref(self.session), C.byref(self.ops), None, 30)
            if name in ('transmit', 'receive'):
                buffer = C.create_string_buffer(data)
                return fn(C.byref(self.session), buffer, len(data))
            return fn(C.byref(self.session))

    def record(name, sink, expected=None):
        assert sink.session.owned == sink.session.active == sink.session.busy == 0
        assert sink.closes == 1
        if expected is not None:
            assert sink.session.status == 0
            encoded = re.findall(rb'transmitraw "([0-9A-F]*)"\r\n', sink.data)
            assert bytes.fromhex(b''.join(encoded).decode()) == expected
            assert sink.data.endswith(b'endproc\r\n')
            compile_source(sink.data.decode('cp437'))
        path = out / (name + '.ASP')
        path.write_bytes(sink.data)
        cases.append(dict(case=name, passed=True, status=sink.session.status,
                          write_error=sink.session.write_error, close_error=sink.session.close_error,
                          writes=sink.writes, closes=sink.closes, source_sha256=sha(path),
                          transmitted_bytes=sink.session.transmitted_bytes,
                          received_bytes=sink.session.received_bytes))

    for name, data, short in [('all-octets', bytes(range(256)), 65535),
                               ('reverse-short-writes', bytes(range(255, -1, -1)), 1)]:
        sink = Sink(short=short)
        assert sink.call('start') == 0
        for at in range(0, len(data), 40):
            assert sink.call('transmit', data[at:at+40]) == 0
        assert sink.call('stop') == sink.call('stop') == 0
        record(name, sink, data)
    for name, prompt in [('quote-caret-FF-prompt', b'\r\n"^> \xff'),
                          ('control-prompt', bytes(range(1, 17))),
                          ('empty-filtered-prompt', b'\0' * 16),
                          ('sliding-prompt', b'0123456789abcdefghijklmnopqrstuvwxyz')]:
        sink = Sink()
        assert sink.call('start') == sink.call('transmit', b'READY>') == 0
        for at in range(0, len(prompt), 16):
            assert sink.call('receive', prompt[at:at+16]) == 0
        assert sink.call('transmit', bytes(range(40))) == sink.call('stop') == 0
        if name == 'empty-filtered-prompt':
            assert b'waitfor ' not in sink.data
        else:
            assert b'waitfor loc_prompt 30\r\nif waitfor == 0\r\nexit\r\nendif\r\n' in sink.data
        if name == 'quote-caret-FF-prompt':
            assert b'strpoke loc_prompt 0 34\r\n' in sink.data
        if name == 'sliding-prompt':
            assert b'klmnopqrstuvwxyz' in sink.data
        record(name, sink, b'READY>' + bytes(range(40)))
    sink = Sink()
    assert sink.call('start') == sink.call('transmit', b'tail') == 0
    before = bytes(sink.data)
    assert sink.call('cancel') == sink.call('stop') == 5
    assert bytes(sink.data) == before and b'transmitraw' not in sink.data
    record('cancel-discards-unpublished-tail', sink)
    for name, options, status, write_error, close_error in [
        ('header-write-error', dict(fail=71), 3, 71, 0),
        ('zero-progress', dict(zero=True), 3, 0, 0),
        ('overreported-write', dict(excess=True), 3, 0, 0),
        ('primary-write-secondary-close', dict(fail=71, close=99), 3, 71, 99),
        ('close-error', dict(close=99), 4, 0, 99)]:
        sink = Sink(**options)
        assert sink.call('start') == (3 if status == 3 else 0)
        assert sink.call('stop') == sink.call('stop') == status
        assert (sink.session.write_error, sink.session.close_error) == (write_error, close_error)
        record(name, sink)
    sink = Sink(reenter=True)
    assert sink.call('start') == sink.call('transmit', b'ABC') == sink.call('stop') == 0
    assert sink.reentered and set(sink.reentered) == {2}
    record('reentrant-close-rejected', sink, b'ABC')
    sink = Sink()
    assert sink.call('stop') == 2
    for timeout in (0, 32768):
        assert lib.aspect_recorder_start(C.byref(sink.session), C.byref(sink.ops), None, timeout) == 1
    assert sink.writes == sink.closes == 0
    assert sink.call('start') == 0
    snapshot = bytes(sink.session)
    for name, count in [('transmit', 41), ('receive', 17)]:
        assert getattr(lib, 'aspect_recorder_' + name)(C.byref(sink.session), None, count) == 1
    assert lib.aspect_recorder_transmit(C.byref(sink.session), None, 1) == 1
    assert sink.call('transmit', b'') == sink.call('receive', b'') == 0
    assert bytes(sink.session) == snapshot
    assert sink.call('stop') == 0
    assert sink.call('transmit', b'A') == 2
    record('argument-and-state-rejections', sink, b'')
    sink = Sink()
    assert sink.call('start') == 0
    sink.session.transmitted_bytes = 0xffffffff
    assert sink.call('transmit', b'A') == 1
    sink.session.received_bytes = 0xffffffff
    assert sink.call('receive', b'A') == 1
    assert sink.call('stop') == 0
    record('input-counter-overflow', sink, b'')
    sink = Sink()
    assert sink.call('start') == 0
    sink.session.source_bytes = 0xffffffff
    writes = sink.writes
    assert sink.call('transmit', b'A' * 40) == 3
    assert sink.writes == writes and sink.call('stop') == 3
    record('source-counter-overflow', sink)
    sink = Sink()
    assert sink.call('start') == sink.call('stop') == 0
    assert lib.aspect_recorder_start(C.byref(sink.session), C.byref(sink.session.ops), None, 30) == 0
    assert sink.call('transmit', b'REUSE') == sink.call('stop') == 0 and sink.closes == 2
    # Two separately closed recordings share this diagnostic sink; only the
    # second remains in session state. Neither close is repeated.
    cases.append(dict(case='reuse-aliased-ops', passed=True, closes=2))
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(out / 'frozen-source' / name) == digest, name
    result = dict(passed=True, case_count=len(cases), cases=cases, inputs=frozen,
                  library_sha256=sha(out / 'recorder.so'), scope=__doc__)
    with (out / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, case_count=len(cases))))


if __name__ == '__main__':
    main()
