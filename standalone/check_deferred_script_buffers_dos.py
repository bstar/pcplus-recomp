#!/usr/bin/env python3
"""Actual DOS deferred buffer failures, six streams and exact PROGRAM snapshots."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--disk',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    names=['src/aspect/script_file_runtime.c','src/aspect/script_file_runtime.h','src/aspect/runtime.h',
           'standalone/deferred_script_buffers_fixture.c','standalone/check_deferred_script_buffers_dos.py']
    if a.disk:names+=['src/aspect/buffer_snapshot.c','src/aspect/buffer_snapshot.h']
    flags=['-dASPECT_DISK_SCRIPT_SNAPSHOTS'] if a.disk else []
    sources={n:sha(ROOT/n) for n in names}
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we',
        '-dASPECT_DEFER_SCRIPT_BUFFERS','-dASPECT_EXTERNAL_PROCESS','-dASPECT_EXTERNAL_UNWIND',*flags,
        '-d_nmalloc=probe_allocate','-d_nfree=probe_free','-dsetvbuf=probe_setvbuf',
        '-fo='+str(out/'backend.obj'),str(ROOT/'src/aspect/script_file_runtime.c')],cwd=out,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-dASPECT_EXTERNAL_PROCESS','-dASPECT_EXTERNAL_UNWIND',*flags,
        *([str(ROOT/'src/aspect/buffer_snapshot.c')] if a.disk else []),
        '-i='+str(ROOT/'src/aspect'),'-fe=BUFFERS.EXE',str(ROOT/'standalone/deferred_script_buffers_fixture.c'),
        str(out/'backend.obj')],cwd=out,check=True)
    config='''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 12000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "'''+str(out)+'''"
c:
BUFFERS > REPORT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=35)
    report=(out/'REPORT.TXT').read_text();m=re.search(r'CHECKS (\d+) FAILURES (\d+) LIVE (\d+) BADFREE (\d+)',report)
    assert process.returncode==0 and m and tuple(map(int,m.groups()[1:]))==(0,0,0),report
    assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    result=dict(passed=True,disk_snapshots=a.disk,checks=int(m[1]),sources=sources,binary_sha256=sha(out/'BUFFERS.EXE'),
        scope=__doc__+' Owned DOS8086 stdio with guarded512-byte buffer allocations, six injected snapshot-allocation failures, open/setvbuf/close failures, exact saved-byte corruption detection, buffered read continuity and partial teardown. Direct adapter component, not full VM, modem or physical acceptance.')
    if a.disk:
        assert not list(out.glob('LPS*.TMP'))
        result['scope']=__doc__+' Actual DOS8086; six original guarded512B buffers, byte-exact disk-backed integrity snapshots with no duplicate buffer allocations, retained buffered reads, corruption detection, partial teardown and no temporary residue. Low-level IO faults separately checked.'
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',m[1],'DOS buffer checks; zero live/double-free allocations')
if __name__=='__main__':main()
