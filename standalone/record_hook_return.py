#!/usr/bin/env python3
"""Bind returned-PRM validation to raw DOS artifacts and reproduced products."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['linked', 'dos', 'proof', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--register-prefix', required=True)
    args = parser.parse_args()
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return'
    probe = base.with_name(base.name + '-probe')
    prior = base.with_name(base.name.removesuffix('-return'))
    sources, custody = {}, {}

    def collect(report):
        for name, digest in report['sources'].items():
            assert name not in sources or sources[name] == digest, name
            assert sha(ROOT / name) == digest, name
            sources[name] = digest

    def capture(path):
        assert path.resolve().is_relative_to(ROOT / 'build')
        custody[str(path.relative_to(ROOT))] = sha(path)

    for folder in [base, probe]:
        manifest = read(folder / 'manifest.json')
        assert manifest['experimental_hook_return'] and manifest['experimental_session_controls']
        assert manifest['experimental_register_handoff'] and not manifest.get('original_inputs')
        assert sha(folder / 'TERMINAL.EXE') == manifest['binary_sha256']
        collect(manifest)
        for name in ['TERMINAL.EXE', 'terminal.map', 'manifest.json', 'hook_return.obj']:
            capture(folder / name)
    binary, diagnostic = sha(base / 'TERMINAL.EXE'), sha(probe / 'TERMINAL.EXE')
    assert 'terminal_session_projection_probe_far' not in (base / 'terminal.map').read_text()
    assert b'HRETURN.BIN' not in (base / 'TERMINAL.EXE').read_bytes()
    layout = inspect_terminal_memory(base / 'TERMINAL.EXE', base / 'terminal.map')
    old = inspect_terminal_memory(prior / 'TERMINAL.EXE', prior / 'terminal.map')
    assert layout['near_bytes'] == old['near_bytes'] == 65520
    def segment(info, name):
        return next(s['bytes'] for s in info['code_segments'] if s['name'] == name)
    assert segment(layout, 'HOOK_CODE') - segment(old, 'HOOK_CODE') == 1749
    assert segment(layout, '_TEXT') - segment(old, '_TEXT') == 22
    old_receipt = read(ROOT / 'docs/validation/session-controls.json')
    old_path = str((prior / 'TERMINAL.EXE').relative_to(ROOT))
    assert sha(prior / 'TERMINAL.EXE') == old_receipt['products'][old_path]
    capture(prior / 'TERMINAL.EXE')
    reports = [args.linked.resolve() / 'result.json', args.dos.resolve() / 'result.json',
               args.proof.resolve() / 'result.json']
    linked, dos, proof = map(read, reports)
    for report, path in zip([linked, dos, proof], reports):
        assert report['passed']
        collect(report); capture(path)
    assert linked['inputs'] == sum(c['inputs'] for c in linked['cases']) == 1995
    assert all(c['passed'] for c in linked['cases']) and linked['binary_sha256'] == binary
    assert dos['hook_return'] and dos['retained_baseline'] and dos['session_controls']
    assert dos['binary_sha256'] == diagnostic and len(dos['cases']) == 5
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values())
        folder = reports[1].parent / case['case']
        raw = (folder / 'AWAY.PRM').read_bytes()
        assert len(raw) == 1264 and raw == (folder / 'PBASE.BIN').read_bytes()
        assert not (folder / 'TEST.PRM').exists()
        seal = 0xb41d ^ 1 ^ 1
        for value in struct.unpack('<632H', raw):
            seal = (((seal << 1) | (seal >> 15)) & 65535) ^ value
        assert (folder / 'BSTATE.BIN').read_bytes() == struct.pack('<4H', 0xb451, 1, 1, seal) + raw
        current = bytearray(raw)
        serial = case['case'] in ('serial', 'serial-inactive')
        struct.pack_into('<H', current, 2, 5 if serial else 6)
        struct.pack_into('<H', current, 0x194, 6 if case['case'].startswith('directory-') else 4)
        if serial:
            struct.pack_into('<H', current, 0x1a4, 350)
        struct.pack_into('<H', current, 0x1bc, int(struct.unpack_from('<H', raw, 0x1bc)[0] == 0))
        struct.pack_into('<HH', current, 0x4e4, 999, 1)
        assert (folder / 'PACTIVE.BIN').read_bytes() == (folder / 'PAGAIN.BIN').read_bytes() == current
        proposed = bytearray(current)
        struct.pack_into('<H', proposed, 0x1ae, 30)
        enabled = int(struct.unpack_from('<H', current, 0x1bc)[0] == 0)
        struct.pack_into('<H', proposed, 0x1bc, 65535 if enabled else 0)
        struct.pack_into('<HH', proposed, 0x4e4, 321, 654)
        struct.pack_into('<H', proposed, 0x42c, 1)
        assert (folder / 'POUT.BIN').read_bytes() == proposed
        plan = (folder / 'HRETURN.BIN').read_bytes()
        assert len(plan) == 490
        assert struct.unpack_from('<3H', plan) == (int(case['case'] in ('MODEM', 'directory-MODEM')), 0xe020, 1)
        assert struct.unpack_from('<H', plan, 24)[0] == 30
        assert struct.unpack_from('<H', plan, 418)[0] == 1
        assert plan[484:] == struct.pack('<3H', enabled, 321, 654)
        assert (folder / 'HRSTAT.BIN').read_bytes() == struct.pack('<4H', 0, 0, 2, 65535)
        assert (folder / 'HREJECT.BIN').read_bytes() == b'X' * 490
        assert (folder / 'HERROR.BIN').read_bytes() == struct.pack('<4H', 6, 0, 2, 0x200)
        assert (folder / 'PSTAT.BIN').read_bytes() == b'\0\0'
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        assert len((folder / 'BEFORE.BIN').read_bytes()) == 42
        assert 'cputype=8086' in (folder / 'dosbox.conf').read_text()
        for artifact in folder.iterdir():
            if artifact.is_file(): capture(artifact)
    regressions = []
    for port in [1, 2]:
        for case in ['normal', 'bad-token', 'missing-script', 'missing-helper', 'divide', 'budget', 'abort']:
            label = f'{args.register_prefix}-{port}-{case}'
            path = ROOT / 'build/register-handoff-dos' / label / 'result.json'
            report = read(path)
            assert report['passed'] and report['hook_return'] and report['session_controls']
            assert (report['port'], report['case'], report['cpu']) == (port, case, '8086')
            assert report['parent_sha256'] == report['DOS']['binary_sha256'] == binary
            assert report['DOS']['passed'] and all(report['DOS']['checks'].values())
            collect(report); capture(path)
            folder = ROOT / 'build/connection-dos' / ('register-' + label)
            for snap in report['snapshots']:
                assert sha(folder / f'OWNER{snap["index"]}.BIN') == snap['owner_sha256']
                assert sha(folder / f'CHILD{snap["index"]}.BIN') == snap['child_sha256']
            for artifact in folder.iterdir():
                if artifact.is_file(): capture(artifact)
            regressions.append(dict(port=port, case=case, snapshots=len(report['snapshots']), passed=True))
    assert proof['original_inputs'] == [] and len(proof['products']) == 6
    assert proof['products'][str((base / 'TERMINAL.EXE').relative_to(ROOT))] == binary
    assert proof['products'][str((probe / 'TERMINAL.EXE').relative_to(ROOT))] == diagnostic
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_directory_keys_source.py')
    for name, digest in proof['products'].items(): assert sha(ROOT / name) == digest
    capture(reports[2].parent / 'build.log')
    for name in ['standalone/record_hook_return.py', 'docs/HOOK_RETURN.md']:
        sources[name] = sha(ROOT / name)
    target = args.output.resolve()
    assert target.is_relative_to(ROOT / 'build') or target.is_relative_to(ROOT / 'docs/validation')
    target.parent.mkdir(parents=True, exist_ok=True)
    result = dict(passed=True, linked_cases=1995, DOS_cases=dos['cases'], register_regressions=regressions,
                  source_files=proof['source_files'], products=proof['products'], terminal_sha256=binary,
                  prior_controls_sha256=sha(prior / 'TERMINAL.EXE'), added_hook_code_bytes=1749,
                  added_resident_code_bytes=22, near_bytes=65520, sources=sources, custody_sha256=custody,
                  scope='Optional supported returned-PRM validation and change classification. Raw DOS rejection/acceptance '
                  'and unchanged active session. No helper EXEC/routing, resource staging, returned adoption, new live BBS '
                  'or physical hardware acceptance. Native evidence is static derived-image inspection only.')
    target.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS1995 linked, five DOS,14 register workflows; six reproduced products')


if __name__ == '__main__':
    main()
