#!/usr/bin/env python3
"""Audit saved DOS multiline captures against independent pyte and libvterm.

This does not run or patch DOS. Raw differences remain failures of exact
agreement. Glyph/background agreement is a separately named observation,
never a replacement for the complete attribute/cursor comparison.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

from test_ansi_reference_dos import ROOT, RESET, reference, sha
from test_ansi_multiline_dos import STAGES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True, action='append')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    executable = output / 'libvterm-reference'
    flags = shlex.split(subprocess.check_output(
        ['pkg-config', '--cflags', '--libs', 'vterm'], text=True))
    command = ['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
        str(ROOT / 'standalone/ansi_libvterm_reference.c'), '-o', str(executable), *flags]
    subprocess.run(command, check=True)
    cases, captures = [], {}
    for folder in args.capture:
        folder = folder.resolve()
        assert folder.is_relative_to(ROOT / 'build')
        producer = json.loads((folder / 'result.json').read_text())
        assert all(value for name, value in producer['checks'].items() if name != 'all_checkpoints')
        payload = RESET
        for number, (label, step) in enumerate(STAGES):
            payload += step
            case = folder / label
            actual = (case / 'SCREEN.BIN').read_bytes()
            assert len(actual) == 4000 and (case / 'input.bin').read_bytes() == payload
            saved = json.loads((case / 'result.json').read_text())
            for name in ['actual_DSR_ready', 'DOS_exit', 'hardware_restored',
                    'PRM_unchanged', 'no_peer_errors', 'status_help_visible']:
                assert saved['checks'][name], (case, name)
            assert (case / 'BEFORE.BIN').read_bytes() == (case / 'AFTER.BIN').read_bytes()
            replies = [[int(a), int(b)] for a, b in re.findall(
                rb'\x1b\[(\d+);(\d+)R', (case / 'serial.bin').read_bytes())]
            assert len(replies) == 1 and replies == saved['actual_cursor_replies']
            expected_pyte, cursor_pyte = reference(payload)
            assert expected_pyte == (case / 'expected.bin').read_bytes()
            cells = output / f'{folder.name}-{number:02}.bin'
            meta = json.loads(subprocess.check_output(
                [str(executable), str(case / 'input.bin'), str(cells)], text=True))
            expected_libvterm = cells.read_bytes()
            assert len(expected_libvterm) == 3840
            comparisons = {}
            for name, expected, cursor in [('pyte', expected_pyte, cursor_pyte),
                    ('libvterm', expected_libvterm, meta['cursor'])]:
                different = [i for i in range(1920)
                    if actual[2*i:2*i+2] != expected[2*i:2*i+2]]
                if name == 'pyte':
                    assert len(different) == saved['different_cells']
                comparisons[name] = dict(different_cells=len(different),
                    cursor=list(cursor), cursor_matches=list(cursor) == replies[0],
                    glyphs_and_backgrounds_match=all(actual[2*i] == expected[2*i]
                        and actual[2*i+1] & 0x70 == expected[2*i+1] & 0x70
                        for i in range(1920)),
                    all_differences_are_blank_foregrounds=all(actual[2*i] == expected[2*i] == 32
                        and actual[2*i+1] & 0xf0 == expected[2*i+1] & 0xf0
                        for i in different),
                    first_differences=[dict(row=i//80+1, column=i%80+1,
                        actual=list(actual[2*i:2*i+2]), expected=list(expected[2*i:2*i+2]))
                        for i in different[:4]])
            cases.append(dict(capture=folder.name, checkpoint=label,
                prefix_bytes=len(payload), actual_cursor=replies[0], comparisons=comparisons))
            for filename in ['input.bin', 'expected.bin', 'SCREEN.BIN', 'BEFORE.BIN',
                    'AFTER.BIN', 'serial.bin', 'result.json', 'TEST.PRM', 'dosbox.conf']:
                path = case / filename
                captures[str(path.relative_to(ROOT))] = sha(path)
        captures[str((folder / 'result.json').relative_to(ROOT))] = sha(folder / 'result.json')
    def aggregate(field):
        return all(c['comparisons'][name][field] for c in cases for name in ['pyte', 'libvterm'])
    library = Path(subprocess.check_output(
        ['pkg-config', '--variable=libdir', 'vterm'], text=True).strip()) / 'libvterm.so'
    header = Path(subprocess.check_output(
        ['pkg-config', '--variable=includedir', 'vterm'], text=True).strip()) / 'vterm.h'
    source_names = ['standalone/audit_ansi_multiline_references.py',
        'standalone/ansi_libvterm_reference.c', 'standalone/test_ansi_multiline_dos.py',
        'standalone/test_ansi_reference_dos.py', 'nix/flake.nix', 'nix/flake.lock']
    result = dict(evidence_valid=True, exact_reference_agreement=all(
        not c['comparisons'][name]['different_cells'] and c['comparisons'][name]['cursor_matches']
        for c in cases for name in ['pyte', 'libvterm']), cases=cases,
        all_glyphs_and_backgrounds_agree=aggregate('glyphs_and_backgrounds_match'),
        only_blank_foreground_differences=aggregate('all_differences_are_blank_foregrounds'),
        all_libvterm_cursors_agree=all(c['comparisons']['libvterm']['cursor_matches'] for c in cases),
        captures=captures, sources={name: sha(ROOT / name) for name in source_names},
        reference_library=dict(path=str(library), sha256=sha(library),
            header_sha256=sha(header), version=meta['version']),
        adapter_sha256=sha(executable), compiler_command=command,
        scope=__doc__ + ' ASCII-only Linux reference adapter. Captures retain their original '
            'source hashes; the later Nix dependency addition does not change their DOS bytes. '
            'No full-profile, all-frame, font-pixel or physical acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Validated', len(cases), 'native checkpoints; exact reference agreement:',
        result['exact_reference_agreement'], '; libvterm cursors:', result['all_libvterm_cursors_agree'],
        '; glyph/background agreement:', result['all_glyphs_and_backgrounds_agree'])


if __name__ == '__main__':
    main()
