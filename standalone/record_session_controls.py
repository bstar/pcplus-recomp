#!/usr/bin/env python3
"""Bind actual sound/mouse projection, DOS images, register recovery and source proof."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from omf_imports import records, externals
from terminal_memory import inspect_terminal_memory

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def sealed(raw):
    value = 0xb41d ^ 1 ^ 1
    for word in struct.unpack('<632H', raw):
        value = (((value << 1) | (value >> 15)) & 65535) ^ word
    return struct.pack('<4H', 0xb451, 1, 1, value) + raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linked', type=Path, required=True)
    parser.add_argument('--dos', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--register-label', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = ROOT / 'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls'
    probe = base.with_name(base.name + '-probe')
    old = base.with_name(base.name.removesuffix('-controls'))
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
        assert manifest['experimental_session_controls'] and manifest['experimental_register_handoff']
        assert not manifest.get('original_inputs') and sha(folder / 'TERMINAL.EXE') == manifest['binary_sha256']
        collect(manifest)
        for name in ['TERMINAL.EXE', 'terminal.map', 'manifest.json', 'session_projection.obj']:
            capture(folder / name)
    binary = sha(base / 'TERMINAL.EXE')
    probe_binary = sha(probe / 'TERMINAL.EXE')
    assert 'terminal_session_projection_probe_far' not in (base / 'terminal.map').read_text()
    assert b'PBASE.BIN' not in (base / 'TERMINAL.EXE').read_bytes()
    layout = inspect_terminal_memory(base / 'TERMINAL.EXE', base / 'terminal.map')
    prior = inspect_terminal_memory(old / 'TERMINAL.EXE', old / 'terminal.map')
    assert layout['near_bytes'] == prior['near_bytes'] == 65520
    assert layout['resident_code_spare_bytes'] == prior['resident_code_spare_bytes']
    new_hook = next(s['bytes'] for s in layout['code_segments'] if s['name'] == 'HOOK_CODE')
    old_hook = next(s['bytes'] for s in prior['code_segments'] if s['name'] == 'HOOK_CODE')
    assert new_hook - old_hook == 156
    legacy = read(ROOT / 'docs/validation/register-bbs.json')['terminal_sha256']
    assert sha(old / 'TERMINAL.EXE') == legacy
    imports = {name.decode() for kind, data, _ in records((base / 'session_projection.obj').read_bytes())
               if kind == 0x8c for name, _ in externals(data)}
    assert imports == {'_hook_session_capture', 'terminal_option_mask', 'terminal_directory_mode',
                       'terminal_directory_context_valid', '_terminal_sound_enabled', '_terminal_mouse_selected_scale',
                       '_prm_project_session', '_hook_baseline_copy', '_terminal_session_project', '_small_code_'}
    linked_path = args.linked.resolve() / 'result.json'
    linked = read(linked_path)
    assert linked['passed'] and linked['session_controls'] and linked['inputs'] == 104
    assert linked['binary_sha256'] == binary
    collect(linked); capture(linked_path)
    dos_path = args.dos.resolve() / 'result.json'
    dos = read(dos_path)
    assert dos['passed'] and dos['session_controls'] and dos['retained_baseline'] and len(dos['cases']) == 5
    assert dos['binary_sha256'] == probe_binary
    collect(dos); capture(dos_path)
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values())
        folder = dos_path.parent / case['case']
        raw = (folder / 'AWAY.PRM').read_bytes()
        assert raw == (folder / 'PBASE.BIN').read_bytes() and len(raw) == 1264
        assert not (folder / 'TEST.PRM').exists() and (folder / 'BSTATE.BIN').read_bytes() == sealed(raw)
        expected = bytearray(raw)
        serial = case['case'] in ('serial', 'serial-inactive')
        struct.pack_into('<H', expected, 2, 5 if serial else 6)
        struct.pack_into('<H', expected, 0x194, 6 if case['case'].startswith('directory-') else 4)
        if serial:
            struct.pack_into('<H', expected, 0x1a4, 350)
        struct.pack_into('<H', expected, 0x1bc, int(struct.unpack_from('<H', raw, 0x1bc)[0] == 0))
        struct.pack_into('<HH', expected, 0x4e4, 999, 1)
        assert (folder / 'POUT.BIN').read_bytes() == expected
        assert (folder / 'PSTAT.BIN').read_bytes() == b'\0\0'
        assert 'cputype=8086' in (folder / 'dosbox.conf').read_text()
        assert len((folder / 'BEFORE.BIN').read_bytes()) == 42
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        for path in folder.iterdir():
            if path.is_file():capture(path)
    regressions = []
    for label in args.register_label:
        path = ROOT / 'build/register-handoff-dos' / label / 'result.json'
        report = read(path)
        assert report['passed'] and report['session_controls'] and report['cpu'] == '8086'
        assert report['parent_sha256'] == binary and report['DOS']['binary_sha256'] == binary
        assert report['DOS']['passed'] and all(report['DOS']['checks'].values())
        collect(report); capture(path)
        folder = ROOT / 'build/connection-dos' / ('register-' + label)
        for snap in report['snapshots']:
            assert sha(folder / f'OWNER{snap["index"]}.BIN') == snap['owner_sha256']
            assert sha(folder / f'CHILD{snap["index"]}.BIN') == snap['child_sha256']
        for artifact in folder.iterdir():
            if artifact.is_file():capture(artifact)
        regressions.append(dict(case=report['case'], port=report['port'], snapshots=len(report['snapshots']), passed=True))
    assert {(r['port'], r['case']) for r in regressions} == {
        (p, c) for p in [1, 2] for c in ['normal', 'bad-token', 'missing-script', 'missing-helper', 'divide', 'budget', 'abort']}
    proof_path = args.proof.resolve() / 'result.json'
    proof = read(proof_path)
    assert proof['passed'] and proof['original_inputs'] == [] and len(proof['products']) == 6
    assert proof['products'][str((base / 'TERMINAL.EXE').relative_to(ROOT))] == binary
    assert proof['products'][str((probe / 'TERMINAL.EXE').relative_to(ROOT))] == probe_binary
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_directory_keys_source.py')
    for name, digest in proof['products'].items():assert sha(ROOT / name) == digest, name
    collect(proof); capture(proof_path); capture(proof_path.parent / 'build.log')
    for name in ['standalone/record_session_controls.py', 'standalone/prove_directory_keys_source.py', 'docs/SESSION_CONTROLS.md']:
        sources[name] = sha(ROOT / name)
    target = args.output.resolve()
    assert target.is_relative_to(ROOT / 'build') or target.is_relative_to(ROOT / 'docs/validation')
    target.parent.mkdir(parents=True, exist_ok=True)
    result = dict(passed=True, linked_cases=104, DOS_cases=dos['cases'], register_regressions=regressions,
                  source_files=proof['source_files'], products=proof['products'], unchanged_BBS_product_sha256=legacy,
                  added_hook_code_bytes=156, near_bytes=65520, imports=sorted(imports), sources=sources,
                  custody_sha256=custody, scope='Optional live sound/accepted mouse preferences over the existing full-image projection. '
                  'No extra PRM frame, near data/code growth or IO in production projection. Diagnostic DOS mutations use '
                  'normal offer/commit before driver acquisition; exact startup baseline remains retained. No returned-helper '
                  'settings application, native unknown-field completion, HOOK routing, live BBS or physical hardware acceptance.')
    target.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS104 linked, five DOS,14 register workflows; six reproduced products; exact older BBS product')


if __name__ == '__main__':
    main()
