#!/usr/bin/env python3
"""Real DOS8086 shared-owner conflicts, recovery, exact accounting and CWD drift."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['accounting-success', 'capture-target', 'capture-stage', 'capture-backup',
         'existing-external-reservation', 'uncertain-capture-owner',
         'directory-close-error-after-release', 'directory-close-error-still-open',
         'install-and-rollback-failure', 'installed-backup-cleanup-failure',
         'stale-record', 'existing-stage', 'invalid-date', 'canonical-error',
         'canonical-over63', 'release-error', 'CWD-change-after-canonicalization',
         'suffix-rejected', 'snapshot-target', 'monitor-target', 'history-target',
         'record-replacement-success']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    build = ROOT/'build/directory-storage'
    manifest = json.loads((build/'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(build/'STORAGE.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT/name) == digest, name
    out.mkdir(parents=True)
    shutil.copyfile(build/'STORAGE.EXE', out/'STORAGE.EXE')
    (out/'sample.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out/'sample.asm'), '-o', str(out/'SNAP.COM')], check=True)
    original = bytes((i*37+11) & 255 for i in range(23050))
    record_start = 250+16*114
    expected = bytearray(original)
    expected[record_start+61:record_start+70] = b'10/25/26\0'
    count = (struct.unpack_from('<H', original, record_start+70)[0]+3) & 65535
    struct.pack_into('<H', expected, record_start+70, count)
    record_change = bytearray(original);record_change[record_start] ^= 0x5a
    (out/'OTHER').mkdir()
    decoy = b'CWD-DECOY-DO-NOT-TOUCH'
    (out/'OTHER/SOURCE.DIR').write_bytes(decoy)
    commands = []
    for mode in range(len(NAMES)):
        case = out/f'T{mode:03}'
        case.mkdir()
        (case/'SOURCE.DIR').write_bytes(original+(b'X' if mode == 17 else b''))
        if mode in (2, 11):(case/'PCPSTG.$$$').write_bytes(b'EXISTING-STAGE')
        if mode == 3:(case/'PCPBAK.$$$').write_bytes(b'EXISTING-BACKUP')
        commands += [f'cd \\T{mode:03}', f'..\\STORAGE {mode} >RESULT.TXT', 'if errorlevel 1 goto failed']
    commands += ['cd \\', 'echo PASS>PASS.TXT', 'goto capture', ':failed',
                 'cd \\', 'echo FAIL>FAIL.TXT', ':capture', 'SNAP A', 'exit']
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
'''+ '\n'.join(commands)+'\n'
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
            env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, timeout=180)
    assert run.returncode == 0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(), \
        [(p.parent.name, p.read_text()) for p in out.glob('T*/RESULT.TXT')]
    before, after = (out/'BEFORE.BIN').read_bytes(), (out/'AFTER.BIN').read_bytes()
    assert len(before) == 42 and before == after
    assert (out/'OTHER/SOURCE.DIR').read_bytes() == decoy
    reports = []
    for mode, name in enumerate(NAMES):
        case = out/f'T{mode:03}'
        fields = struct.unpack('<7H', (case/'RESULT.BIN').read_bytes())
        assert fields[0] == mode
        state = (case/'STATE.BIN').read_bytes()
        assert len(state) == 222
        phase, status, dos, claim, release = struct.unpack_from('<5H', state)
        replacement = dict(zip('status dos close cleanup rollback bytes installed backup stage source'.split(),
                               struct.unpack_from('<10H', state, 10)))
        assert fields[1] == status or mode == 12 and fields[1] == 1 and status == 0
        installed = mode in (0, 9, 15, 16, 21)
        held = mode in (6, 7, 8, 9, 15)
        assert bool(replacement['installed']) == installed
        assert (phase == 3) == held
        if mode == 8:
            assert not (case/'SOURCE.DIR').exists()
            assert (case/'PCPBAK.$$$').read_bytes() == original
        else:
            target = record_change if mode == 21 else expected if installed else original+(b'X' if mode == 17 else b'')
            assert (case/'SOURCE.DIR').read_bytes() == target, name
        if mode == 9:assert (case/'PCPBAK.$$$').read_bytes() == original
        if mode == 3:assert (case/'PCPBAK.$$$').read_bytes() == b'EXISTING-BACKUP'
        if mode not in (3, 8, 9):assert not (case/'PCPBAK.$$$').exists()
        if mode in (2, 11):assert (case/'PCPSTG.$$$').read_bytes() == b'EXISTING-STAGE'
        else:assert not (case/'PCPSTG.$$$').exists()
        baseline = bytearray(original[record_start:record_start+114])
        if mode == 10:baseline[0] ^= 1
        if installed and mode != 21:baseline = expected[record_start:record_start+114]
        assert (case/'BASELINE.BIN').read_bytes() == baseline, name
        assert fields[5] == (4 if fields[3] else 0)
        if mode in (1, 2, 3, 4, 5, 18, 19, 20):assert fields[3] == 0 and claim == 2
        if mode in (12, 13, 14):assert fields[3] == fields[4] == 0
        if mode == 12:assert fields[6] == 0
        if mode == 13:assert status == 4 and dos == 5
        if mode == 14:assert status == 5
        if mode == 15:assert release == 2
        reports.append(dict(case=name, mode=mode, passed=True, status=fields[1],
            state=phase, assertions=fields[2], core_closes=fields[3], renames=fields[4],
            admission_witnesses=fields[5], canonical_calls=fields[6], replacement=replacement))
    report = dict(passed=True, binary_sha256=manifest['binary_sha256'],
        case_count=len(reports), native_assertions=sum(r['assertions'] for r in reports),
        cases=reports, hardware_restored=True, CWD_decoy_preserved=True,
        sources=manifest['sources'], test_sources={n: sha(ROOT/n) for n in
            ['standalone/test_directory_storage_dos.py', 'standalone/test_terminal.py']},
        artifacts={str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()},
        original_inputs=[], limitations=manifest['limitations'])
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS', len(reports), 'DOS workflows /', report['native_assertions'], 'native assertions')


if __name__ == '__main__':
    main()
