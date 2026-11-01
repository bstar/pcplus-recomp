#!/usr/bin/env python3
"""Replay cumulative multiline editor prefixes through the real DOS UART.

Each checkpoint starts an unchanged application and replays the complete prefix,
then stops incoming bytes at an actual CPR and captures the normal exit screen.
This measures intermediate semantic checkpoints without instrumenting product
memory. It is deliberately not an every-frame or continuous-session claim.
"""
import argparse
import importlib.metadata
import inspect
import json
from pathlib import Path

from test_ansi_reference_dos import ROOT, RESET, run, sha


STAGES = [
    ('numbered-document', b''.join(
        f'\x1b[{row};1HROW {row:02} | '.encode() +
        bytes([ord('A') + (row - 1) % 26]) * 60
        for row in range(1, 25))),
    ('editor-margins', b'\x1b[5;20r\x1b[20;1H'),
    ('forward-scroll', b''.join(
        f'\r\nNEW {row:02} | '.encode() + b'forward ' * 7
        for row in range(1, 19))),
    ('reverse-scroll', b'\x1b[5;1H' + b''.join(
        b'\x1bM' + f'REVERSE {row:02}'.encode() + b'\r'
        for row in range(1, 7))),
    ('insert-delete-lines', b'\x1b[10;1H\x1b[3LINSERT A\r\nINSERT B'
        b'\x1b[16;1H\x1b[2M'),
    ('multiline-character-edits', b'\x1b[8;10HABCDEFGHIJKLM'
        b'\x1b[8;13H\x1b[3@xyz\x1b[8;20H\x1b[2P'
        b'\x1b[19;78H123456789\r\nTAIL'),
    ('origin-relative-edit', b'\x1b[?6h\x1b[2;4HRELATIVE'
        b'\x1b[16;1H\r\nORIGIN SCROLL\x1b[?6l'),
    ('restore-full-screen', b'\x1b[r\x1b[24;1H\r\nFULL SCROLL'
        b'\x1b[1;1HHEADER\x1b[24;68HEND OF DOCUMENT'),
    ('colored-document', RESET + b''.join(
        f'\x1b[{row};1H\x1b[{30 + row % 8};{40 + (row + 3) % 8}m'.encode() +
        f'COLOR ROW {row:02} | '.encode() + b'colored cells ' * 4
        for row in range(1, 25)) + b'\x1b[0m'),
    ('colored-scroll-and-lines', b'\x1b[6;19r\x1b[19;1H' + b''.join(
        f'\x1b[0m\r\n\x1b[1;{30 + row % 8}mNEW COLOR {row:02}'.encode()
        for row in range(1, 17)) + b'\x1b[0m\x1b[9;1H\x1b[2L'
        b'\x1b[14;1H\x1b[3M'),
    ('colored-reverse-and-wrap', b'\x1b[6;1H\x1bM\x1bM'
        b'\x1b[1;35mREVERSE\x1b[19;79HXYZ\x1b[0m\x1b[r'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fragment', type=int, default=7)
    args = parser.parse_args()
    package, output = args.package.resolve(), args.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    assert 0 < args.fragment <= 4096
    manifest = json.loads((package / 'manifest.json').read_text())
    binary = package / 'PCPLUSSE/TERMINAL.EXE'
    assert sha(binary) == manifest['files']['TERMINAL.EXE']
    source_names = ['standalone/test_ansi_multiline_dos.py',
        'standalone/test_ansi_reference_dos.py', 'standalone/test_terminal.py',
        'standalone/directory_fixtures.py', 'standalone/modem_fixtures.py',
        'standalone/terminal_config_fixtures.py', 'nix/flake.nix', 'nix/flake.lock']
    sources_before = {name: sha(ROOT / name) for name in source_names}
    manifest_before = sha(package / 'manifest.json')
    package_before = {name: sha(package / 'PCPLUSSE' / name) for name in manifest['files']}
    assert package_before == manifest['files']
    output.mkdir(parents=True)
    payload, reports = RESET, []
    for label, step in STAGES:
        payload += step
        report = run(binary, output / label, label, payload, args.fragment)
        report.update(prefix_bytes=len(payload), prefix_sha256=sha(output / label / 'input.bin'))
        reports.append(report)
    checks = dict(all_checkpoints=all(r['passed'] for r in reports),
        sources_unchanged=sources_before == {name: sha(ROOT / name) for name in source_names},
        manifest_unchanged=manifest_before == sha(package / 'manifest.json'),
        package_unchanged=package_before == {
            name: sha(package / 'PCPLUSSE' / name) for name in manifest['files']})
    modules = ['pyte.screens', 'pyte.streams', 'pyte.graphics', 'pyte.charsets',
        'pyte.modes', 'pyte.control', 'pyte.escape', 'wcwidth.wcwidth']
    result = dict(passed=all(checks.values()), checks=checks, cases=reports,
        binary_sha256=sha(binary), package_manifest_sha256=sha(package / 'manifest.json'),
        fragment_bytes=args.fragment, compared_cell_pairs=1920 * len(reports),
        sources=sources_before, package_files=package_before,
        reference_modules={name: sha(Path(inspect.getfile(__import__(name, fromlist=['_']))))
            for name in modules}, pyte_version=importlib.metadata.version('pyte'),
        wcwidth_version=importlib.metadata.version('wcwidth'), original_inputs=[],
        scope=__doc__ + ' Profile6 ANSI, 80x24 CP437 character/attribute cells. '
            'No font pixels, BBS navigation, other emulations, unpaced pressure, '
            'physical modem or every-intermediate-frame acceptance.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    assert result['passed'], 'Independent reference differences retained in ' + str(output)


if __name__ == '__main__':
    main()
