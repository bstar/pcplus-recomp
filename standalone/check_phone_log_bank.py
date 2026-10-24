#!/usr/bin/env python3
"""Audit banked logger runtime, compiler adapters, terminal fit and damaged ABI rejection."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile

from omf_imports import rename_imports
from record_phone_log_file import records
from terminal_memory import inspect_terminal_memory

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['terminal', 'dos', 'source', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--application-evidence', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--fixed-reservation', type=Path)
    parser.add_argument('--reservation-baseline', type=Path)
    args = parser.parse_args()
    build = ROOT / 'build/phone-log-bank'
    manifest = read(build / 'manifest.json')
    dos_path, source_path, terminal = args.dos.resolve(), args.source.resolve(), args.terminal.resolve()
    assert all(path.is_relative_to(ROOT / 'build') for path in [dos_path, source_path, terminal])
    dos, source = read(dos_path / 'checks.json'), read(source_path / 'checks.json')
    assert dos['passed'] and all(dos['checks'].values()) and dos['variant'] == 'bank' and len(dos['cases']) == 9
    assert source['passed'] and source['outputs'] == manifest['outputs'] and source['source_count'] == 24
    assert not source['original_inputs'] and not manifest['original_inputs']
    assert source['sources'] == manifest['sources'] and not (source_path / 'source/analysis').exists()
    assert source['verifier_sha256'] == sha(ROOT / 'standalone/prove_phone_log_queue.py')
    assert dos['binary_sha256'] == manifest['outputs']['bank']['binary_sha256'] == sha(build / 'QUEUE.EXE')
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest == sha(source_path / 'source' / name)
    for name, digest in manifest['outputs']['bank']['objects'].items():
        assert sha(build / name) == digest == sha(source_path / 'source/build/phone-log-bank' / name)
    for name, adapter in manifest['adapters'].items():
        compiler = build / Path(name).with_suffix('.compiler.obj')
        assert sha(compiler) == adapter['compiler_sha256']
        before = compiler.read_bytes()
        aliases = {name: {'__U4D': 'phone_u4div_service_', '__U4M': 'phone_u4mul_service_'}[name]
                   for name in adapter['import_counts']}
        after, counts = rename_imports(before, aliases) if aliases else (before, {})
        assert counts == adapter['import_counts'] and after == (build / name).read_bytes()
        raw = records((build / Path(name).with_suffix('.raw.obj')).read_bytes())
        normalized = records(before)
        assert raw[0][0] == normalized[0][0] == 0x80 and raw[1:] == normalized[1:]
    native_assertions = 0
    for case in range(9):
        row = dos['cases'][str(case)]
        assert row['passed'] and all(row['checks'].values())
        match = re.fullmatch(rb'PASS (\d+) queue assertions\r\n', (dos_path / f'T{case:03}/RESULT.TXT').read_bytes())
        assert match
        native_assertions += int(match[1])
    app = read(terminal / 'manifest.json')
    binary, map_path = terminal / 'TERMINAL.EXE', terminal / 'terminal.map'
    assert app['experimental_phone_log_bank'] and app['binary_sha256'] == sha(binary)
    assert 'standalone/phone_log_bank_client.asm' not in app['sources']
    for name, digest in app['sources'].items():
        assert sha(ROOT / name) == digest, name
    memory = inspect_terminal_memory(binary, map_path)
    assert memory == app['memory_layout']
    raw, listing = binary.read_bytes(), map_path.read_text()
    header = struct.unpack_from('<14H', raw)
    start = header[4] * 16
    symbols = {name: (int(seg, 16), int(off, 16)) for seg, off, name in
               re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
    def offset(name):
        seg, off = symbols[name]
        return start + seg * 16 + off
    assert all('_' + name not in symbols for name in manifest['entries']), 'Diagnostic near entries linked into application'
    mutations = []
    for name in manifest['entries']:
        symbol = '_' + name + '_far'
        bad = bytearray(raw)
        bad[offset(symbol)] ^= 1
        mutations.append((symbol + ':frame', bad, listing))
    for index, site in enumerate(memory['phone_log_callback_sites']):
        for field in [1, 3]:
            bad = bytearray(raw)
            bad[start + site + field] ^= 1
            mutations.append((f'callback-{index}-target-{field}', bad, listing))
        bad = bytearray(raw)
        for index2 in range(header[3]):
            off, seg = struct.unpack_from('<HH', bad, header[12] + index2 * 4)
            if seg * 16 + off == site + 3:
                struct.pack_into('<HH', bad, header[12] + index2 * 4, 0, 0)
                break
        else:
            raise AssertionError('Missing expected callback relocation')
        mutations.append((f'callback-{index}-relocation', bad, listing))
    for name, delta in [('phone_dos_write_service_', 6), ('phone_dos_write_service__resident', 5),
                        ('_phone_log_queue_store', 0), ('_phone_log_queue_store', 665)]:
        bad = bytearray(raw)
        bad[offset(name) + delta] ^= 1
        mutations.append((name + ':byte-' + str(delta), bad, listing))
    if memory['capture_reservation_initialized_bytes'] == 74:
        assert args.fixed_reservation and args.reservation_baseline
        for delta in [8, 10, 73]:
            bad = bytearray(raw)
            bad[offset('_capture_reservation') + delta] ^= 1
            mutations.append(('fixed-reservation-state-' + str(delta), bad, listing))
        for name in ['_capture_file_claim', '_capture_file_unclaim']:
            bad_map = re.sub(r'(?m)^[0-9a-f]{4}:([0-9a-f]{4})([*+ ]+\s+' + name + r'\s*)$',
                             lambda match: '0000:' + match[1] + match[2], listing)
            assert bad_map != listing
            mutations.append((name + ':wrong-segment', raw, bad_map))
    rejected = []
    with tempfile.TemporaryDirectory(prefix='phone-log-bank-audit-') as temporary:
        folder = Path(temporary)
        for name, bad, bad_map in mutations:
            (folder / 'BAD.EXE').write_bytes(bad)
            (folder / 'BAD.map').write_text(bad_map)
            try:
                inspect_terminal_memory(folder / 'BAD.EXE', folder / 'BAD.map')
            except AssertionError:
                rejected.append(name)
            else:
                raise AssertionError('Damaged ABI accepted: ' + name)
    application_path = args.application_evidence.resolve()
    assert application_path.is_relative_to(ROOT / 'build')
    application = read(application_path)
    assert application['passed'] and all(application['checks'].values())
    assert application['terminal_sha256'] == sha(binary) and len(application['cases']) == 2
    for report in application['cases']:
        assert report['passed'] and all(report['checks'].values()) and report['cpu'] == '8086'
        assert report['binary_sha256'] == sha(binary)
        path = ROOT / 'build/connection-dos' / report['case'] / 'result.json'
        assert read(path) == report
    baseline = args.baseline.resolve()
    assert baseline.is_relative_to(ROOT / 'build')
    assert sha(baseline) == '2978657cb75ac29067796c98d81ff253b91eee96b995924d266d05bdfbae471c'
    artifacts = {}
    for report in [dos, source, application]:
        for name, digest in report.get('sources', {}).items():
            assert sha(ROOT / name) == digest
        for name, digest in report.get('inputs', {}).items():
            assert sha(ROOT / name) == digest
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest
            artifacts[name] = digest
    for path in [build / 'manifest.json', build / 'QUEUE.EXE', dos_path / 'checks.json',
                 source_path / 'checks.json', binary, map_path, terminal / 'manifest.json', application_path, baseline]:
        artifacts[str(path.relative_to(ROOT))] = sha(path)
    fixed = legacy = None
    if args.fixed_reservation:
        folder = args.fixed_reservation.resolve()
        legacy_folder = args.reservation_baseline.resolve()
        assert folder.is_relative_to(ROOT / 'build') and legacy_folder.is_relative_to(ROOT / 'build')
        fixed, legacy = read(folder / 'checks.json'), read(legacy_folder / 'result.json')
        assert fixed['passed'] and all(fixed['checks'].values()) and len(fixed['cases']) == 4
        assert not fixed['original_inputs'] and sum(row['assertions'] for row in fixed['cases'].values()) == 446
        assert all(row['passed'] and all(row['checks'].values()) for row in fixed['cases'].values())
        assert legacy['passed'] and all(legacy['checks'].values()) and len(legacy['logs']) == 6
        for report, source_key in [(fixed, 'sources'), (legacy, 'inputs')]:
            for name, digest in report[source_key].items():
                assert sha(ROOT / name) == digest
        for name, digest in fixed['artifacts'].items():
            assert sha(ROOT / name) == digest
            artifacts[name] = digest
        for name, digest in legacy['captures_sha256'].items():
            path = legacy_folder / name
            assert sha(path) == digest
            artifacts[str(path.relative_to(ROOT))] = digest
        for path in [folder / 'checks.json', legacy_folder / 'result.json']:
            artifacts[str(path.relative_to(ROOT))] = sha(path)
    names = ['standalone/check_phone_log_bank.py', 'standalone/prove_phone_log_queue.py',
             'standalone/test_phone_log_queue_dos.py', 'standalone/terminal_memory.py',
             'standalone/test_connection_dos.py', 'standalone/test_terminal.py',
             'standalone/test_phone_log_bank_terminal.py', 'Makefile',
             'tools/build', 'tools/dev', 'nix/flake.nix', 'nix/flake.lock']
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  DOS=dos, source_rebuild=source, native_assertions=native_assertions,
                  terminal_sha256=sha(binary), memory=memory, rejected_mutations=rejected,
                  application_tests=application, unchanged_baseline_sha256=sha(baseline), artifacts=artifacts,
                  fixed_reservation=fixed, legacy_reservation=legacy,
                  sources={name: sha(ROOT / name) for name in names},
                  limitations=['Logger bank linked but no terminal event/startup/reservation/poll hooks yet.',
                               'Actual DOS banked queue/rollback tests and selected synthetic serial terminal regressions; no real modem/card acceptance.',
                               'Clean source reproduction covers the logger diagnostic/objects, not a new whole-application clean-source proof.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Audited nine banked DOS cases/', native_assertions, 'assertions, source rebuild,',
          len(rejected), 'rejected ABI mutations and', len(application['cases']), 'terminal cases')


if __name__ == '__main__':
    main()
