#!/usr/bin/env python3
"""Compare bare FROMDDIR/MONO integer operands with frozen original, host and DOS compiler outcomes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/aspect'))
from compiler import CompileError, compile_source

ORIGINAL_COMPILER = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
NAMES = ('fromddir', 'mono')
CONTEXTS = ('assignment', 'casefold', 'long', 'string', 'condition', 'local',
            'parameter', 'readonly', 'reserved', 'function')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    folder, out = a.compiler.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest = json.loads((folder/'manifest.json').read_text())
    assert manifest['original_inputs'] == []
    assert manifest['binary_sha256'] == sha(folder/'ASPCOMP.EXE')
    for name, digest in manifest['sources'].items():
        assert sha(ROOT/name) == digest, name
    fixture = ROOT/'standalone/fixtures/aspect_state_builtin_compiler_vectors.json'
    oracle = json.loads(fixture.read_text())
    cases = oracle['cases']
    assert oracle['compiler_sha256'] == ORIGINAL_COMPILER
    assert len(cases) == 20 and sum(c['success'] for c in cases) == 12
    assert {c['label'] for c in cases} == {n+'-'+k for n in NAMES for k in CONTEXTS}
    out.mkdir(parents=True)
    shutil.copyfile(folder/'ASPCOMP.EXE', out/'ASPCOMP.EXE')
    batch = ['@echo off']
    for i, case in enumerate(cases):
        assert hashlib.sha256(case['source'].encode('cp437')).hexdigest() == case['source_sha256']
        try:
            actual = compile_source(case['source'])
            success = True
        except CompileError:
            actual, success = b'', False
        assert success == case['success'], case['label']
        if success:
            expected = bytes.fromhex(case['hex'])
            assert actual == expected, case['label']
            assert hashlib.sha256(expected).hexdigest() == case['asx_sha256']
        else:
            assert case['errors'], case['label']
        name = f'P{i:05}'
        (out/(name+'.ASP')).write_bytes(case['source'].replace('\n', '\r\n').encode('cp437'))
        batch.extend([f'ASPCOMP {name}.ASP >{name}.LOG',
                      f'if errorlevel 1 echo REJECT>{name}.RES',
                      f'if not errorlevel 1 echo ACCEPT>{name}.RES'])
    batch.append('echo COMPLETE>DONE.TXT')
    (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode('ascii'))
    (out/'dosbox.conf').write_text(
        '[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\n'
        'cycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n'
        f'mount c "{out}"\nc:\ncall RUN.BAT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, check=True, timeout=60)
    assert (out/'DONE.TXT').read_text().strip() == 'COMPLETE'
    records = []
    for i, case in enumerate(cases):
        name = f'P{i:05}'
        success = (out/(name+'.RES')).read_text().strip() == 'ACCEPT'
        target = out/(name+'.ASX')
        assert success == case['success'] == target.exists(), case['label']
        if success:
            assert target.read_bytes() == bytes.fromhex(case['hex']), case['label']
            assert sha(target) == case['asx_sha256'], case['label']
        records.append(dict(label=case['label'], accepted=success,
                            source_sha256=case['source_sha256'],
                            asx_sha256=sha(target) if success else None,
                            log_sha256=sha(out/(name+'.LOG'))))
    sources = dict(manifest['sources'])
    for path in (Path(__file__), fixture, ROOT/'src/aspect/compiler.py'):
        sources[str(path.relative_to(ROOT))] = sha(path)
    result = dict(passed=True, case_count=len(records), accepted=12, rejected=8,
        original_compiler_sha256=ORIGINAL_COMPILER, binary_sha256=manifest['binary_sha256'],
        compiler_manifest_sha256=sha(folder/'manifest.json'), sources=sources,
        original_inputs=[], cases=records,
        scope=__doc__+' Each operand is exercised in assignment, case folding, long arithmetic, '
              'string rejection, condition, local assignment, integer parameter, read-only target, '
              'reserved declaration and call syntax. Original observations are frozen authored '
              'source fixtures; this checker executes only the source-built DOS CLI. '
              'No runtime getter, parent service, hardware or full-language parity claim.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS20 original FROMDDIR/MONO operand compiler cases:12 accepted,8 rejected')


if __name__ == '__main__':
    main()
