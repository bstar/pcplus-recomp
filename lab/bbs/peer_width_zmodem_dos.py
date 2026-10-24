#!/usr/bin/env python3
"""Actual wide-view DOS ZMODEM against pinned independent lrzsz."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
from types import SimpleNamespace
import sys
import time

from product_inputs import ROOT, select_product
sys.path.insert(0, str(ROOT / 'standalone'))
import test_terminal_zmodem_dos as base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WidePeer:
    def expect_reply(self, reply, timeout=5):
        deadline = time.monotonic() + timeout
        while len(self.pending) < len(reply) and time.monotonic() < deadline and not self.stop.is_set():
            self.receive()
        assert bytes(self.pending[:len(reply)]) == reply, (bytes(self.pending), reply)
        del self.pending[:len(reply)]

    def ready(self):
        super().ready()
        self.send(b'\x1b[?3h\x1b[2;121HBEFORE!\x1b[6n')
        self.expect_reply(b'\x1b[2;128R')
        self.checks['actual_wide_before_protocol'] = True
        self.log('wide-before-protocol')

    def resume(self):
        self.send(b'\x1b[2;121HRESUMED\x1b[6n')
        self.expect_reply(b'\x1b[2;128R')
        self.checks['actual_wide_after_protocol'] = True
        self.log('wide-after-protocol')
        # One status query suffices. Repeated probes followed by discarding the
        # pending buffer can split and lose a still-arriving reply prefix.
        self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\x1b[5n')
        self.expect_reply(b'\x1b[0n')
        self.checks['posttransfer_DSR'] = True
        self.expect_reply(b'ready', timeout=self.resume_timeout)
        self.checks['posttransfer_keyboard'] = True
        self.send(b'\x1b[?3l\x1b[HAFTER TRANSFER\x1b[2;73HNARROW!\x1b[6n')
        self.expect_reply(b'\x1b[2;80R')
        self.checks['actual_narrow_after_keyboard'] = True
        self.log('narrow-after-keyboard')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--case', choices=['rx-default', 'rx-crc16', 'tx-default', 'tx-escape'], required=True)
    p.add_argument('--automatic', action='store_true')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.automatic or a.case.startswith('rx-')
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    output = a.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    source = Path(base.__file__).read_text()
    for token in ['cputype=386', 'BatchPeer.resume(self);', "ADDKEY {' '.join(keys)}"]:
        assert source.count(token) == 1
    source = source.replace('cputype=386', 'cputype=8086').replace('BatchPeer.resume(self);', 'self.resume();')
    source = source.replace("ADDKEY {' '.join(keys)}", "ADDKEY p900 enter {' '.join(keys)}")
    config_line = [line for line in source.splitlines() if line.startswith('  config_image=image(')]
    assert len(config_line) == 1
    source = source.replace(config_line[0], '  config_image=wide_config(' + config_line[0].split('=', 1)[1] + ')')
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    def wide_config(image):
        result = bytearray(image)
        if manifest.get('experimental_mouse'):
            struct.pack_into('<HH', result, 0x4e4, 8, 4)
        if manifest.get('experimental_custom_irq'):
            struct.pack_into('<HH', result, 0x184, 4, 3)
        return bytes(result)
    scope = dict(base.__dict__)
    exec(compile(source, base.__file__, 'exec'), scope)
    # Keep the original run implementation and substitute only its peer class.
    # Its actual run method must dispatch to the width-aware resume override.
    class SelectedPeer(WidePeer, scope['ZPeer']):
        run = scope['ZPeer'].run
    scope.update(BINARY=binary, OUT=output, ZPeer=SelectedPeer, wide_config=wide_config)
    flags = {'rx-default': [], 'rx-crc16': ['-o'], 'tx-default': [], 'tx-escape': ['-e']}[a.case]
    files = [('EMPTY.BIN', b''), ('ODD.BIN', b'A'), ('ALL.BIN', bytes(range(256)) * 257 + b'\0\x1a\xff@\r')]
    recipe = dict(name=a.case, direction=a.case[:2], flags=flags, files=files,
                  automatic=a.automatic, sender_helper=None, transfer_timeout=65,
                  zedzap=False, resume_timeout=45)
    options = SimpleNamespace(label='wide', sha256=sha(binary), after_ms=35000, timeout=85,
                              receive_credit=256 if a.automatic else None, sender_helper_sha256=None)
    executable = Path(shutil.which('sz' if a.case.startswith('rx-') else 'rz')).resolve()
    peer_identity = dict(path=str(executable), sha256=sha(executable))
    inputs += [binary, Path(__file__), ROOT / 'lab/bbs/product_inputs.py']
    inputs += [ROOT / 'standalone' / name for name in [
        'test_terminal_zmodem_dos.py', 'test_terminal_transfer_dos.py',
        'test_terminal_ymodem_dos.py', 'test_terminal.py', 'check_zmodem.py',
        'check_zmodem_wire.py', 'terminal_config_fixtures.py']]
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    result = scope['run_case'](recipe, options)
    result['checks']['inputs_unchanged'] = frozen == {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    result['checks']['independent_peer_unchanged'] = sha(executable) == peer_identity['sha256']
    result['passed'] = all(result['checks'].values())
    report = dict(passed=result['passed'], result=result, automatic=a.automatic, inputs=frozen,
                  binary_sha256=sha(binary), peer=peer_identity,
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in output.rglob('*') if path.is_file()},
                  scope='Actual8086 DOS ZMODEM/automatic receive with wide replies before and after independent lrzsz protocol, manual keyboard and narrow recovery. Synthetic files; no stock BBS/audio/physical acceptance.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=result['checks']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
