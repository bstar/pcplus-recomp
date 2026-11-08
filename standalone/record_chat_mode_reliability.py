#!/usr/bin/env python3
"""Bind current packaged bytes to BUSY/endurance and verified transfer recovery."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts = {}

    def read(name):
        path = ROOT / name
        result = json.loads(path.read_text())
        assert result['passed'], name
        receipts[name] = sha(path)
        for field in ('sources', 'captures'):
            for source, digest in result.get(field, {}).items():
                assert sha(ROOT / source) == digest, source
        return result

    package_path = ROOT / 'docs/validation/chat-mode-package.json'
    package = json.loads(package_path.read_text())
    assert package['checkpoint_verified'] and len(package['files']) == 17
    products = package['files']
    parent = products['TERMINAL.EXE']
    receipts[str(package_path.relative_to(ROOT))] = sha(package_path)
    bbs_path = ROOT / 'docs/validation/chat-mode-bbs.json'
    bbs = json.loads(bbs_path.read_text())
    assert bbs['checkpoint_verified']
    assert all(products[name] == digest for name, digest in bbs['products'].items())
    receipts[str(bbs_path.relative_to(ROOT))] = sha(bbs_path)
    busy = read('build/busy-retry-dos/chat-mode-reliability-20261108/result.json')
    assert busy['terminal_sha256'] == parent
    assert [case['case'] for case in busy['cases']] == ['busy-exit', 'busy-redial', 'three-calls']
    busy_cases = []
    for case in busy['cases']:
        native = read(case['result'])
        folder = (ROOT / case['result']).parent
        assert native['binary_sha256'] == parent and native['cpu'] == '8086' and all(native['checks'].values())
        count = {'busy-exit': 1, 'busy-redial': 2, 'three-calls': 3}[case['case']]
        assert native['commands'] == ['ATZ', 'ATDCaseTest:23'] * count
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        if count == 3:
            wire = (folder / 'serial.bin').read_bytes()
            assert wire.count(b'\x1b[1;16R') == wire.count(b'\x1b[?1;2c') == 3
            assert all(wire.count(word + b'\r') == 1 for word in (b'one', b'two', b'three'))
        busy_cases.append(dict(case=case['case'], attempts=count, checks=native['checks']))
    endurance = read('build/terminal-endurance/chat-mode-reliability-20261108/result.json')
    native = read(endurance['native_result'])
    assert endurance['terminal_sha256'] == native['binary_sha256'] == parent
    assert endurance['acceptance_duration'] and endurance['seconds'] == 300 and endurance['frames'] == 601
    assert native['seconds'] >= 300 and all(native['checks'].values())
    folder = (ROOT / endurance['native_result']).parent
    wire = (folder / 'serial.bin').read_bytes().replace(b'\x11', b'').replace(b'\x13', b'')
    assert re.findall(rb'\x1b\[\d+;\d+R', wire) == [b'\x1b[1;16R'] + [f'\x1b[{2+i%16};80R'.encode() for i in range(601)]
    assert wire.count(b'ready\r') == 1
    expected, last = [], {}
    for index in range(601):
        row = 2 + index % 16
        text = (f'FRAME {index:04d} ROW {row:02d} ' + ''.join(chr(65+(index+j)%26) for j in range(79))).encode()[:79]
        expected.append(f'\x1b[{row};1H'.encode()+text+b'\x1b[6n')
        last[row] = text
    assert (folder/'flow-payload.bin').read_bytes() == b''.join(expected)
    screen = (folder/'SCREEN.BIN').read_bytes()
    for row, text in last.items():
        start = (row-1)*160
        assert screen[start:start+158:2] == text and screen[start+1:start+158:2] == bytes([7])*79
    assert (folder/'BEFORE.BIN').read_bytes() == (folder/'AFTER.BIN').read_bytes()
    cancel = read('build/chat-mode-cancel-audit-20261108/result.json')
    assert cancel['terminal_sha256'] == parent and cancel['payload_bytes'] == 65539
    assert cancel['partial_disk_bytes'] == 4096 and cancel['exact_retry'] and cancel['same_DOS_process']
    cancellation = read('build/bbs-lab/results/enigma/chat-mode-cancel-retry-20261108/cancel-checks.json')
    assert all(cancellation['checks'].values()) and not cancellation['errors']
    carrier = read('build/bbs-lab/results/enigma/chat-mode-live-carrier-v2-20261108/carrier-checks.json')
    audit = read('build/chat-mode-carrier-audit-20261108/result.json')
    assert audit['terminal_sha256'] == parent and audit['partial_disk_bytes'] == 4096 and audit['exact_retry_bytes'] == 65539
    assert carrier['live_source'] and carrier['cpu'] == '386' and carrier['explicit_UMB']
    assert not carrier['startup_probe'] and not carrier['exec_probe']
    assert carrier['startup_source']['initial_ASX_absent'] and not carrier['startup_source']['compile_before_parent']
    assert all(carrier['checks'].values()) and not carrier['errors']
    for name, product in carrier['products'].items():
        assert products[name] == product['sha256'] == sha(ROOT / product['path'])
    controls = []
    for name, count in [('chat-mode-cancel-controls-20261108', 9), ('chat-mode-carrier-controls-20261108', 16)]:
        control = read('build/' + name + '/result.json')
        assert len(control['cases']) == count
        assert all(case['passed'] and case['rejected'] == (case['case'] != 'unchanged') for case in control['cases'])
        controls.append(dict(name=name, cases=control['cases']))
    result = dict(checkpoint_verified=True, tool_source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), files=products,
        busy_and_reconnect=busy_cases, endurance=dict(seconds=300, frames=601, actual_seconds=native['seconds'], scope=endurance['scope']),
        cancellation={key: cancel[key] for key in ('partial_disk_bytes', 'payload_bytes', 'same_DOS_process', 'authenticated_sessions', 'proxy_connections', 'exact_retry')},
        carrier={key: audit[key] for key in ('cpu', 'live_source', 'explicit_UMB', 'partial_disk_bytes', 'exact_retry_bytes', 'sessions', 'scope')},
        carrier_checks=carrier['checks'], controls=controls, receipts=receipts,
        sources={'standalone/record_chat_mode_reliability.py': sha(Path(__file__).resolve())},
        installed_changed=False, selector_changed=False, physical_verified=False,
        scope='Current17-file candidate. Actual DOS with synthetic Hayes for BUSY/endurance/cancellation; DOSBox native modem/DCD plus actual SynthModem Telnet proxy for live-source carrier/redial retry. Owned stock Enigma; no SIP/audio, physical CTS saturation or hardware acceptance.',
        excluded=['Initial carrier run added the optional20962-byte conventional-memory witness absent from the established passing profile. No ASX/login/retry completed; final DOS/hardware restoration passed. Removing that witness restores early source compilation/login; only the separately audited complete v2 may count as recovery acceptance. Exact DOS error for the witness failure was not captured.'])
    (ROOT / 'docs/validation/chat-mode-reliability.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified current BUSY/three-call/endurance/cancel/carrier software recovery')


if __name__ == '__main__':
    main()
