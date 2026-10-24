#!/usr/bin/env python3
"""Replay frozen parent IRQ artifacts before publishing composed acceptance."""
import argparse
import json
from pathlib import Path
import struct

from build_guarded_helper import ROOT
from package_special_edition import sha
from prove_parent_custom_irq_source import PRODUCTS, CONTROLS
from test_register_handoff_dos import assigned, reset, seal
from test_hook_apply_dos import FIELDS
from test_parent_custom_irq_dos import SETUP_CASES
from check_setup_model import image
from compiler import compile_source


def word(raw, offset, value):
    result = bytearray(raw)
    struct.pack_into('<H', result, offset, value)
    return bytes(result)


def frozen(folder, records):
    for relative, digest in records.items():
        assert sha(folder / relative) == digest, (folder, relative)


def merge_sources(destination, incoming):
    frozen(ROOT, incoming)
    for name, digest in incoming.items():
        assert name not in destination or destination[name] == digest, name
        destination[name] = digest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos', type=Path, required=True)
    p.add_argument('--source-proof', type=Path, required=True)
    p.add_argument('--compile', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    dos_root = args.dos.resolve()
    cohort = json.loads((dos_root / 'result.json').read_text())
    linked_path = ROOT / 'build/parent-custom-irq-linked/result.json'
    linked = json.loads(linked_path.read_text())
    assert cohort['passed'] and len(cohort['cases']) == 28
    assert linked['passed'] and linked['inputs'] == 324
    proof_path = args.source_proof.resolve()
    proof = json.loads(proof_path.read_text())
    assert proof['passed'] and proof['controls'] == CONTROLS and proof['original_inputs'] == []
    assert proof['checker_sha256'] == sha(ROOT / 'standalone/prove_parent_custom_irq_source.py')
    assert proof['build_log_sha256'] == sha(proof_path.parent / 'build.log')
    for folder, leaf in PRODUCTS.items():
        assert sha(ROOT / 'build' / folder / leaf) == proof['products'][folder]
        assert sha(proof_path.parent / 'source/build' / folder / leaf) == proof['products'][folder]
    sources = {}
    for group in (proof, linked, cohort):
        merge_sources(sources, group['sources'])
    raw_artifacts = {}
    snapshots = 0
    groups = {'setup': 0, 'register': 0, 'helper': 0}
    for entry in cohort['cases']:
        report_path = ROOT / entry['report']
        assert sha(report_path) == entry['report_sha256']
        report = json.loads(report_path.read_text())
        assert report['passed'] and all(report.get('checks', {'passed': True}).values())
        merge_sources(sources, report.get('sources', {}))
        raw_artifacts[str(report_path.relative_to(ROOT))] = sha(report_path)
        name = entry['case']
        if name.startswith('setup-'):
            groups['setup'] += 1
            folder = report_path.parent
            for leaf, key in [('TERMINAL.EXE', 'terminal_sha256'), ('PRMEDIT.EXE', 'editor_sha256')]:
                assert sha(folder / leaf) == report[key] == cohort['products'][leaf]
            source, target, source_irq, target_irq, accept = SETUP_CASES[name[6:]]
            raw = word(word(word(word(image(), 0, source - 1), 0x184 + (source - 1) * 2, source_irq),
                            0x4e4, 8), 0x4e6, 4)
            expected = word(word(raw, 0, target - 1), 0x184 + (target - 1) * 2, target_irq)
            assert (folder / 'TEST.PRM').read_bytes() == expected
            selected = target if accept else source
            assert report['selected'] == selected
            assert report['physical_irqs'][selected - 1] == (target_irq if accept else source_irq)
            config = (folder / 'dosbox.conf').read_text()
            assert 'cputype=8086\n' in config
            assert f'serial{selected}=nullmodem irq:{report["physical_irqs"][selected - 1]} ' in config
            for i in range(1, 5):
                a, b = [(folder / (n + str(i) + '.BIN')).read_bytes() for n in ('BEFORE', 'AFTER')]
                assert len(a) == 42 and a == b
            assert (folder / 'SCREEN.BIN').read_bytes()[:30:2] == b'PORT READY LIVE'
            wire = (folder / 'serial.bin').read_bytes()
            for token in (b'\x1b[0n', b'\x1b[1;11R', b'\x1b[?62;2c', b'ready', b'\x1b[1;16R'):
                assert token in wire
        elif name.startswith('register-'):
            groups['register'] += 1
            assert report['cpu'] == '8086' and report['irq'] in (5, 7)
            assert report['DOS']['serial_irq'] == report['irq'] and report['DOS']['passed']
            folder = ROOT / 'build/connection-dos' / report['DOS']['case']
            for leaf, key in [('TERMINAL.EXE', 'parent_sha256'), ('ASPECT.EXE', 'child_sha256')]:
                path = report_path.parent / 'package' / leaf
                assert sha(path) == report[key] == cohort['products'][leaf]
                raw_artifacts[str(path.relative_to(ROOT))] = sha(path)
            zero = bytes(830)
            first, _, _ = assigned(zero, 1)
            second, _, _ = assigned(first, 2)
            failed = report['case'] in ('bad-token', 'divide', 'budget', 'abort')
            expected = [(zero, zero), (zero, first), (first, reset(first))]
            if failed:
                expected += [(first, second), (first, reset(first))]
            expected += [(first, second), (second, reset(second))]
            tokens, epochs = [1, 1, 2, 2, 3], [0, 0, 1, 1, 2]
            if failed:
                tokens, epochs = [1, 1, 2, 2, 3, 3, 4], [0, 0, 1, 1, 1, 1, 3]
            elif report['case'] in ('missing-script', 'missing-helper'):
                tokens, epochs = [1, 1, 3, 3, 4], [0, 0, 1, 1, 3]
            assert len(report['snapshots']) == len(expected)
            for i, (accepted, live) in enumerate(expected):
                owner = (folder / f'OWNER{i}.BIN').read_bytes()
                assert len(owner) == 1734 and struct.unpack_from('<4H', owner) == (1, tokens[i], epochs[i], seal(accepted, epochs[i]))
                assert owner[904:] == accepted and owner[74:904] == reset(accepted)
                assert (folder / f'CHILD{i}.BIN').read_bytes() == live
                snapshots += 1
            wire = (folder / 'serial.bin').read_bytes()
            assert wire.index(b'OBSERVE\r') < wire.rindex(b'\x1b[0n')
            assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        else:
            groups['helper'] += 1
            assert name.startswith('helper-')
            folder = report_path.parent
            assert sha(folder / 'TERMINAL.EXE') == report['binary_sha256'] == cohort['products']['TERMINAL.EXE']
            assert sha(folder / 'APPLYCH.EXE') == report['helper_sha256']
            assert (folder / 'COUNT.BIN').read_bytes() == struct.pack('<H', 3)
            before = [(folder / f'B{i}.BIN').read_bytes() for i in range(3)]
            after = [(folder / f'A{i}.BIN').read_bytes() for i in range(3)]
            committed = report['mode'] == 0
            assert report['committed'] == committed and report['status'] == (0 if committed else 107)
            assert before[1] == (after[0] if committed else before[0])
            assert before[2] == after[1] == before[1]
            for i in range(3):
                assert len(before[i]) == len(after[i]) == 2094
                state = (folder / f'S{i}.BIN').read_bytes()
                assert len(state) == sum(size for _, size in FIELDS)
                fields = {}
                offset = 0
                for field, size in FIELDS:
                    fields[field] = state[offset:offset + size]
                    offset += size
                hardware = struct.unpack('<17H', (folder / f'H{i}.BIN').read_bytes())
                prm = before[i][830:]
                selected = struct.unpack_from('<H', prm)[0]
                irq = struct.unpack_from('<H', prm, 0x184 + selected * 2)[0]
                assert irq in (5, 7) and hardware[8] & (1 << irq)
                at = {5: 13, 7: 15}[irq]
                assert hardware[at:at + 2] == tuple(struct.unpack('<H', fields[n])[0]
                        for n in ('uart_previous_irq_offset', 'uart_previous_irq_segment'))
                if i:
                    owner = fields['_terminal_register_owner']
                    assert owner[904:] == before[i][:830] and struct.unpack_from('<H', owner)[0] == 0
                    assert struct.unpack_from('<H', owner, 4)[0] == (i if committed else i - 1)
            assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
            if report['online']:
                assert report['peer']['passed'] and report['peer']['serial_irq'] in (5, 7)
                wire = (folder / 'serial.bin').read_bytes()
                assert wire.index(b'observe\r') < wire.rindex(b'\x1b[0n')
            else:
                assert (folder / 'BEFORE2.BIN').read_bytes() == (folder / 'AFTER2.BIN').read_bytes()
        for path in folder.iterdir():
            if path.is_file():
                raw_artifacts[str(path.relative_to(ROOT))] = sha(path)
    assert groups == {'setup': 4, 'register': 14, 'helper': 10} and snapshots == 86
    compile_path = args.compile.resolve() / 'result.json'
    compilation = json.loads(compile_path.read_text())
    assert compilation['passed'] and len(compilation['cases']) == 8
    assert compilation['checker_sha256'] == sha(ROOT / 'standalone/test_parent_irq_compile_dos.py')
    compile_matrix = set()
    for entry in compilation['cases']:
        path = ROOT / entry['report']
        assert sha(path) == entry['report_sha256']
        report = json.loads(path.read_text())
        assert report['passed'] and report['connection']['passed']
        assert report['connection']['serial_irq'] == entry['irq']
        assert report['products']['TERMINAL.EXE'] == cohort['products']['TERMINAL.EXE']
        assert report['products']['ASPECT.EXE'] == cohort['products']['ASPECT.EXE']
        assert report['products']['ASPCOMP.EXE'] == proof['products']['aspect-compiler-dos']
        frozen(ROOT, report['artifacts'])
        merge_sources(sources, report['sources'])
        for leaf, digest in report['products'].items():
            assert sha(path.parent / leaf) == digest
        folder = ROOT / 'build/connection-dos' / report['connection']['case']
        wire = (folder / 'serial.bin').read_bytes()
        assert wire.index(b'observe\r') < wire.rindex(b'\x1b[0n')
        assert wire.count(b'COMPILED\r') == (0 if report['case'] == 'rejected' else 1)
        if report['case'] == 'rejected':
            assert not (folder / 'LOGON.ASX').exists()
        else:
            for asp in folder.glob('*.ASP'):
                assert asp.with_suffix('.ASX').read_bytes() == compile_source(asp.read_text())
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        compile_matrix.add((report['port'], report['case']))
        raw_artifacts[str(path.relative_to(ROOT))] = sha(path)
        raw_artifacts.update(report['artifacts'])
    assert compile_matrix == {(port, case) for port in (1, 2) for case in ('explicit', 'fallback', 'chain', 'rejected')}
    for name in ('standalone/record_parent_custom_irq.py', 'standalone/prove_parent_custom_irq_source.py',
                 'standalone/prove_custom_irq_source.py', 'standalone/test_parent_irq_compile_dos.py'):
        sources[name] = sha(ROOT / name)
    frozen(ROOT, sources)
    result = dict(passed=True, original_inputs=[], sources=sources, artifacts=raw_artifacts,
                  linked=linked, dos=cohort, compilation=compilation, source_reproduction=proof, groups=groups, register_snapshots=snapshots,
                  scope='Optional composed parent/editor/ASIOv7/helper IRQ5/7 software acceptance:324 linked '
                  'inputs,28 DOS8086 owner workflows,eight bare nested compiler workflows,86 exact register snapshots and eight source-reproduced products. '
                  'Five standard controls remain exact. Current stock BBS, arbitrary compiler/native parity, '
                  'physical/shared IRQs and Special Edition/card deployment remain separate gates.')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PASS parent IRQ receipt:324 linked,28 owners+8 compilers,86 snapshots and eight source products')


if __name__ == '__main__':
    main()
