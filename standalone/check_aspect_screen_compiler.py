#!/usr/bin/env python3
"""Compare native screen/cursor command grammar with frozen original, host and DOS compiler outcomes."""
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
    fixtures = [ROOT/'standalone/fixtures'/leaf for leaf in (
        'aspect_screen_compiler_vectors.json', 'aspect_numeric_register_compiler_vectors.json')]
    cases = [];oracles = []
    for fixture, count, accepted in zip(fixtures, (1173, 221), (387, 170)):
        oracle = json.loads(fixture.read_text())
        assert oracle['compiler_sha256'] == ORIGINAL_COMPILER
        assert len(oracle['cases']) == count and sum(c['success'] for c in oracle['cases']) == accepted
        if 'command_grammar' in oracle:
            assert set(oracle['command_grammar']) == {'box', 'clear', 'home', 'locate', 'scroll', 'getvattr', 'putvattr'}
        cases += oracle['cases']
        oracles.append(dict(fixture=fixture.name, cases=count, accepted=accepted, rejected=count-accepted))
    assert len({c['source_sha256'] for c in cases}) == 1394
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
    for path in (Path(__file__), *fixtures, ROOT/'src/aspect/compiler.py'):
        sources[str(path.relative_to(ROOT))] = sha(path)
    result = dict(passed=True, case_count=len(records), accepted=557, rejected=837, oracles=oracles,
        original_compiler_sha256=ORIGINAL_COMPILER, binary_sha256=manifest['binary_sha256'],
        compiler_manifest_sha256=sha(folder/'manifest.json'), sources=sources,
        original_inputs=[], cases=records,
        scope=__doc__+'1394 authored sources derived from1426 original DOS8086 observations over '
              'all seven commands, required/optional arities, every operand type/position, writable '
              'integer destinations, local/parameter storage, atomic-expression refusals, signed '
              'decimal bounds, raw hexadecimal width/wrapping and exact punctuation boundaries. '
              'N0..N9 assignment/expressions/procedure arguments, signed long promotion and nonaliasing '
              'prefix controls are also frozen original observations. This checker executes only source-built '
              'DOS CLI programs. No native runtime, clipping, geometry, hardware or full-language claim.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS1394 original screen/N-bank compiler cases:557 accepted,837 rejected')


if __name__ == '__main__':
    main()
