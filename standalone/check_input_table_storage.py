#!/usr/bin/env python3
"""Compare actual CS/DS input tables across independent code/data relocations."""
import argparse
import hashlib
import itertools
import json
import re
from pathlib import Path
import subprocess
from check_input_dispatch import MissingInputService
from check_input_dispatch_relocation import RelocatedInput

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def observe(binary, mapping, value, mono, c1, input_mode):
    machine = RelocatedInput(binary, mapping)
    for name, setting in [('attributes_monochrome', mono),
                          ('terminal_c1_enabled', c1),
                          ('terminal_input_mode_8fe8', input_mode)]:
        machine.put(name, setting)
    missing = None
    try:
        # Real stream context is important: selected C1 entries unread their
        # byte and re-enter the escape parser, rather than directly rendering.
        machine.feed(b'A' + bytes([value]) + b'B')
    except MissingInputService as error:
        missing = error.args
    fields = ['screen_cursor_row', 'screen_cursor_column', 'screen_video_offset',
              'csi_wrap_pending', 'scroll_suppress_next_linefeed',
              'terminal_history_pending', 'terminal_history_wrapped',
              'ansi_input_position', 'ansi_parameter_canary']
    return (bytes(machine.uc.mem_read(machine.video, 4000)), machine.history(),
            tuple(machine.get(name) for name in fields), machine.calls,
            machine.positions, missing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    manifest = json.loads((ROOT / 'build/input_dispatch/manifest.json').read_text())
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    sources = [ROOT / name for name in manifest['sources'] if name.endswith('.asm')]
    objects = {}
    for variant in ('code', 'data'):
        target = out / variant
        target.mkdir()
        objects[variant] = []
        for index, source in enumerate(sources):
            obj = target / f'unit-{index}.obj'
            options = []
            if source.parent.parent == ROOT / 'reconstruction':
                options += ['-D' + source.parent.name.upper() + '_OMF']
            if variant == 'data' and source == ROOT / 'reconstruction/input_dispatch/dispatch.asm':
                options += ['-DINPUT_TABLES_DATA']
            subprocess.run(['nasm', '-f', 'obj', *options, '-I',
                            str(ROOT / 'reconstruction/uart') + '/', '-I',
                            str(ROOT / 'reconstruction/ansi') + '/',
                            str(source), '-o', str(obj)], check=True)
            objects[variant].append(str(obj))
    cases = []
    for codepad, datapad in [(0, 0), (0x333, 0x555), (0x2111, 0x1234)]:
        pair = {}
        for variant in objects:
            target = out / variant / f'{codepad:x}-{datapad:x}'
            target.mkdir()
            asm, obj = target / 'pad.asm', target / 'pad.obj'
            asm.write_text(f'BITS 16\nSEGMENT _TEXT public class=CODE use16\n'
                           f'times {codepad} db 0xcc\n'
                           f'SEGMENT _DATA public align=16 class=DATA use16\n'
                           f'times {datapad} db 0xa5\n')
            subprocess.run(['nasm', '-f', 'obj', str(asm), '-o', str(obj)], check=True)
            binary, mapping = target / 'INPUT.EXE', target / 'input.map'
            subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option',
                            'map=' + str(mapping), 'name', str(binary), 'file',
                            ','.join([str(obj)] + objects[variant])], check=True)
            pair[variant] = (binary, mapping)
        sizes = {}
        for variant, (_, mapping) in pair.items():
            sizes[variant] = {}
            for segment in ('_TEXT', '_DATA'):
                match = re.search(r'^' + segment + r'\s+\S+\s+\S+\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)', mapping.read_text(), re.M | re.I)
                assert match, segment
                sizes[variant][segment] = int(match[1], 16)
        # A disabled/no-op flag must not pass the behavioral comparison alone.
        # 108 pointer bytes plus two removed CS prefixes leave resident code.
        assert sizes['code']['_TEXT'] - sizes['data']['_TEXT'] == 110, sizes
        assert sizes['data']['_DATA'] - sizes['code']['_DATA'] >= 108, sizes
        count = 0
        for mono, c1, mode, value in itertools.product((0, 1), (0, 1), (0, 1), range(256)):
            expected = observe(*pair['code'], value, mono, c1, mode)
            actual = observe(*pair['data'], value, mono, c1, mode)
            assert actual == expected, (codepad, datapad, mono, c1, mode, value)
            count += 1
        cases.append(dict(code_padding=codepad, data_padding=datapad,
                          compared_streams=count, passed=True,
                          segment_sizes=sizes,
                          binaries={name: sha(paths[0]) for name, paths in pair.items()}))
        print('PASS input table placement', hex(codepad), hex(datapad), count, flush=True)
    result = dict(passed=True, cases=cases,
                  compared_streams=sum(case['compared_streams'] for case in cases),
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  checker_sha256=sha(Path(__file__)),
                  scope=__doc__,
                  limitations=['Linked CPU replay with memory serial and modeled BIOS; not DOS startup or physical UART acceptance.',
                               'Explicit unsupported services must fail identically in both placements.'])
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
