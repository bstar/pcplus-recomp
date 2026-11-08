#!/usr/bin/env python3
"""8086 DOS ownership/failure test of the real Help allocator with stub services.

Tests the allocator's refusal and retry behavior, not the RPC transport,
malformed pointer publication, parent MCB admission or full application unwind.
"""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 names=['src/help/resource_heap.c','src/help/resource_heap.h','src/aspect/resident_render.h','src/aspect/runtime.h','standalone/help_snapshot_allocator_diagnostic.c','standalone/test_help_snapshot_allocator_dos.py']
 sources={n:sha(ROOT/n) for n in names}
 for n in names:
  dst=out/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
 stage=out/'source'
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dASPECT_HELP_PARENT_SNAPSHOT','-dASPECT_SNAPSHOT_LEASE','-k8192','-fm=HALLOC.map','-fe=HALLOC.EXE',str(stage/'standalone/help_snapshot_allocator_diagnostic.c'),str(stage/'src/help/resource_heap.c')],cwd=out,check=True)
 (out/'dosbox.conf').write_text(f'''[sdl]
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
c:
HALLOC >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:
  r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
 raw=(out/'OUTPUT.TXT').read_bytes();m=re.fullmatch(rb'HELPALLOC checks=22 failures=0\r\n',raw)
 checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),ownership_and_failure_assertions=bool(m),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()))
 result=dict(passed=all(checks.values()),checks=checks,self_checks=22 if m else None,sources=sources,binary_sha256=sha(out/'HALLOC.EXE'),original_inputs=[],physical_verified=False,scope=__doc__)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['passed'],checks,raw);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
