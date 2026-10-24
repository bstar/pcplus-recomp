#!/usr/bin/env python3
"""Seal native call-log identity, CPU policy, DOS FILE behavior and clean rebuild."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    build = ROOT / 'build/phone-log'
    manifest = read(build / 'manifest.json')
    cpu = read(build / 'cpu-checks.json')
    proof_path = ROOT / 'reconstruction/phone_log/provenance.json'
    proof = read(proof_path)
    assert proof['bytes'] == 258 and proof['start'] == 0xe2a9 and proof['end'] == 0xe3ab
    assert sha(build / 'controller.bin') == proof['sha256']
    assert manifest['exact_bytes'] == 258 and not manifest['original_inputs']
    assert sha(build / 'PHONELOG.EXE') == manifest['binary_sha256']
    assert cpu['passed'] and cpu['inputs'] == 384 and cpu['sha256'] == proof['sha256']
    assert cpu['original_verified'], 'Bind the separately requested original-byte comparison'
    dos_path = a.dos.resolve()
    source_path = a.source.resolve()
    assert all(path.is_relative_to(ROOT / 'build') for path in [dos_path, source_path])
    dos = read(dos_path / 'checks.json')
    source = read(source_path / 'checks.json')
    assert dos['passed'] and all(dos['checks'].values())
    assert source['passed'] and source['source_count'] == 7 and source['CPU_inputs'] == 384
    assert not source['original_inputs']
    assert source['binary_sha256'] == dos['binary_sha256'] == manifest['binary_sha256']
    fresh = source_path / 'source'
    assert not (fresh / 'analysis').exists()
    assert read(fresh / 'build/phone-log/cpu-checks.json')['original_verified'] is False
    assert sha(fresh / 'build/phone-log/PHONELOG.EXE') == manifest['binary_sha256']
    assert (dos_path / 'RESULT.TXT').read_bytes() == b'PASS 33 DOS phone-log checks\r\n'
    before = (dos_path / 'BEFORE.BIN').read_bytes()
    assert len(before) == 42 and before == (dos_path / 'AFTER.BIN').read_bytes()
    heading = b'\r\n' + b'NAME'.ljust(36) + b'NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
    line = b'\r\n' + b'LoC LAB'.ljust(22) + b' ' + b'5550100'.rjust(20) + b' 10/24/26 12:34:56 12:35:58 00:01:02'
    assert (dos_path / 'NEW.FON').read_bytes() == heading + line * 2
    artifacts = {}
    for mapping in [manifest['sources'], cpu['sources'], dos['sources'], dos['inputs']]:
        for name, digest in mapping.items():
            assert sha(ROOT / name) == digest, name
    for name, digest in source['sources'].items():
        assert sha(ROOT / name) == sha(fresh / name) == digest
    for report in [dos, source]:
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest, name
            artifacts[name] = digest
    for path in [build / 'manifest.json', build / 'cpu-checks.json', build / 'PHONELOG.EXE',
                 build / 'controller.bin', dos_path / 'checks.json', source_path / 'checks.json', proof_path]:
        artifacts[str(path.relative_to(ROOT))] = sha(path)
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  native=proof, CPU=cpu, DOS=dos, source_rebuild=source, artifacts=artifacts,
                  binary_sha256=manifest['binary_sha256'], recorder_sha256=sha(Path(__file__)),
                  workflow_sources={name: sha(ROOT / name) for name in [
                      'Makefile', 'nix/flake.nix', 'nix/flake.lock', 'tools/dev', 'tools/build',
                      'standalone/prove_phone_log.py', 'standalone/record_phone_log.py']},
                  correction='PCPLUS.FON is the native telephone-call log; its extension is not font-format evidence.',
                  limitations=['Native controller is recovered; DOS diagnostic uses explicit synthetic clock/date and direct path callbacks, not full native clock/path/UI providers.',
                               'Native formatted-write/close errors are ignored and pending state can outlive a missing file. Production reliable persistence remains required.',
                               'Not connected to the terminal scheduler, UART or modem lifecycle. PRM setting import, reconnect/cancellation integration, physical acceptance and F01-F16 remain open.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Sealed258 native bytes,384 policy inputs,33 DOS checks,7-source rebuild and', len(artifacts), 'artifacts')


if __name__ == '__main__':
    main()
