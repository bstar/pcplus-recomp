#!/usr/bin/env python3
"""Check declared package identities and execute its DOS compiler/runner."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
from build_native_mouse import ROOT,sha
from test_terminal import SAMPLER


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='package-'+uuid.uuid4().hex)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    package=ROOT/'build/dos-package-mouse';manifest=json.loads((package/'manifest.json').read_text())
    assert manifest['original_inputs']==[] and manifest['experimental_mouse'] and len(manifest['files'])==10
    assert all(sha(package/p)==h for p,h in manifest['files'].items())
    assert all(sha(ROOT/p)==h for p,h in manifest['sources'].items())
    for leaf,info in manifest['input_manifests'].items():
        path=ROOT/info['manifest'];assert sha(path)==info['sha256']
        assert json.loads(path.read_text())['binary_sha256']==sha(package/leaf)
    out=ROOT/'build/package-mouse-tests'/args.label;out.mkdir(parents=True,exist_ok=False)
    for name in manifest['files']:shutil.copyfile(package/name,out/name)
    (out/'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
ASPCOMP HELLO.ASP REBUILD.ASX >COMPILE.TXT
if errorlevel 1 goto failed
ASPECT REBUILD.ASX >RUN.TXT
if errorlevel 1 goto failed
ASPECT HELLO.ASP >SOURCE.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
SNAP S
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],
            cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
            stdout=log,stderr=log,timeout=25)
    checks=dict(emulator_exit=result.returncode==0,DOS_exit=(out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),
        DOS_compiler_exact=(out/'REBUILD.ASX').exists() and (out/'REBUILD.ASX').read_bytes()==(package/'HELLO.ASX').read_bytes(),
        inputs_unchanged=all(sha(out/p)==h for p,h in manifest['files'].items()),
        packaged_sources_unchanged=all(sha(ROOT/p)==h for p,h in manifest['sources'].items()))
    screen=(out/'SCREEN.BIN').read_bytes() if(out/'SCREEN.BIN').exists() else b''
    output=b''.join((out/p).read_bytes() for p in ('RUN.TXT','SOURCE.TXT') if(out/p).exists())+screen[::2]
    checks['actual_script_message']=b'ASPECT script ready' in output
    report=dict(passed=all(checks.values()),checks=checks,package_manifest_sha256=sha(package/'manifest.json'),
        files=manifest['files'],checker_sha256=sha(Path(__file__)),
        sampler_sha256=sha(ROOT/'standalone/test_terminal.py'),
        artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
        scope='Declared source-built package files; actual8086 DOS source compiler, compiled runner and automatic source compilation. Terminal/settings interaction has separate acceptance; no physical hardware or full application claim.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Mouse package:', 'PASS' if report['passed'] else checks,out)
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
