#!/usr/bin/env python3
"""Independently check linked, DOS and source artifacts for the child IRQ extension."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from prove_custom_irq_source import ROOT, PRODUCTS, CONTROLS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sources(sources):
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos', type=Path, required=True)
    p.add_argument('--source-proof', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    child = ROOT / 'build/aspect-serial-custom-irq'
    host = json.loads((child / 'custom-irq-checks.json').read_text())
    legacy = json.loads((child / 'checks.json').read_text())
    assert host['passed'] and host['inputs'] == 309 and legacy['passed'] and legacy['inputs'] == 108
    assert all(c['passed'] for c in host['cases']) and all(c['passed'] for c in legacy['groups'])
    assert host['legacy_checks_sha256'] == sha(child / 'checks.json')
    assert host['binary_sha256'] == sha(child / 'SERIAL.EXE')
    check_sources(host['sources'])
    proof_path = args.source_proof.resolve()
    proof = json.loads(proof_path.read_text())
    assert proof['passed'] and proof['controls'] == CONTROLS and proof['original_inputs'] == []
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_custom_irq_source.py')
    assert proof['build_log_sha256'] == sha(proof_path.parent / 'build.log')
    check_sources(proof['sources'])
    for folder, leaf in PRODUCTS.items():
        assert sha(ROOT / 'build' / folder / leaf) == proof['products'][folder]
        assert sha(proof_path.parent / 'source/build' / folder / leaf) == proof['products'][folder]
    dos_root = args.dos.resolve()
    dos = json.loads((dos_root / 'result.json').read_text())
    assert dos['passed'] and len(dos['cases']) == 29
    sources = dict(proof['sources'])
    sources.update(host['sources'])
    matrix = set()
    full = 0
    mismatches = 0
    for report in dos['cases']:
        # Resolve the frozen case by its unique artifact set and deterministic
        # matrix name; never infer success from the final DOS exit alone.
        matches = [f for f in dos_root.iterdir() if f.is_dir() and (f / 'result.json').is_file()
                   and json.loads((f / 'result.json').read_text()) == report]
        assert len(matches) == 1
        folder = matches[0]
        assert report['passed'] and report['cpu'] == '8086'
        check_sources(report['sources'])
        sources.update(report['sources'])
        for name, digest in report['artifacts'].items():
            assert sha(folder / name) == digest, (folder.name, name)
        assert (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists()
        before, after = [(folder / (n + '.BIN')).read_bytes() for n in ('BEFORE', 'AFTER')]
        assert len(before) == 42 and before == after
        config = (folder / 'dosbox.conf').read_text()
        serial_line = next(s for s in config.splitlines() if s.startswith('serial' + str(report['port']) + '='))
        assert ' irq:' + str(report['physical_irq']) + ' ' in serial_line
        assert 'cputype=8086\n' in config
        flow = report['flow']
        wrong = report['deliberate_mismatch']
        wire = (b'\x11' if flow in ('S', 'B') else b'') + b'D' + (b'' if wrong else b'R') + (b'\x13' if flow in ('S', 'B') else b'')
        assert (folder / 'serial.bin').read_bytes() == wire and report['wire_hex'] == wire.hex()
        product = 'aspect-register-parent-custom-irq' if report['full_VM'] else 'aspect-serial-custom-irq'
        assert report['binary_sha256'] == proof['products'][product]
        if wrong:
            assert not report['full_VM'] and report['physical_irq'] != report['lease_irq']
            assert (folder / 'RESULT.TXT').read_bytes() == b'status=23 count=0\r\n'
            mismatches += 1
        else:
            assert report['physical_irq'] == report['lease_irq']
            if not report['full_VM']:
                assert (folder / 'RESULT.TXT').read_bytes() == b'status=0 count=0\r\n'
                if flow == 'N' and not report['legacy_option']:
                    matrix.add((report['port'], report['physical_irq']))
        full += bool(report['full_VM'])
    assert matrix == {(p, i) for p in range(1, 5) for i in (3, 4, 5, 7)}
    assert full == 5 and mismatches == 2
    # Inspect the actual bank adapter: five WORDs from a far C caller, a near
    # call to the real backend, stack reset and far return. The ordinary build
    # still has its original four-argument bytes, proven by its exact hash.
    base = ROOT / 'build/aspect-register-parent-custom-irq'
    m = json.loads((base / 'manifest.json').read_text())
    assert m['experimental_custom_irq'] and m['experimental_register_handoff']
    image = (base / 'ASPECT.EXE').read_bytes()
    header = struct.unpack_from('<H', image, 8)[0] * 16
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in
               re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
                          (base / 'ASPECT.map').read_text(), re.M | re.I)}
    seg, off = symbols['_serial_bank_backend_open_resident']
    expected = bytes.fromhex('5589e5') + b''.join(bytes([0xff, 0x76, 8 + 2 * i]) for i in reversed(range(5)))
    body = image[header + seg * 16 + off:header + seg * 16 + off + len(expected) + 8]
    assert body.startswith(expected) and body[len(expected)] == 0xe8
    target_seg, target_off = symbols['_aspect_serial_backend_open']
    assert seg == target_seg and (off + len(expected) + 3 + struct.unpack_from('<h', body, len(expected) + 1)[0]) & 65535 == target_off
    assert body[len(expected) + 3:] == bytes.fromhex('8d66005dcb')
    for name in ('standalone/record_custom_irq.py', 'standalone/prove_custom_irq_source.py'):
        sources[name] = sha(ROOT / name)
    result = dict(passed=True, sources=sources, original_inputs=[], linked=host, legacy=legacy,
                  source_reproduction=proof, dos=dos, five_word_bank_callback_hex=body.hex(),
                  artifacts={str(f.relative_to(ROOT)): sha(f) for f in [child / 'custom-irq-checks.json',
                             child / 'checks.json', dos_root / 'result.json', proof_path]},
                  scope='Optional child lease only:309 targeted+108 legacy modeled inputs,29 DOS8086 '
                  'workflows including two deliberate mismatch timeouts, five-product source reproduction '
                  'and three exact controls. Parent PRM/setup/handoff, shared IRQs, physical UARTs and full application acceptance remain open.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS child IRQ receipt:309 targeted,108 legacy,29 DOS and five reproduced products')


if __name__ == '__main__':
    main()
