#!/usr/bin/env python3
"""Compare shared/default resource scans in actual8086 DOS, with old assertions."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha
from build_path_session import object_segments
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 sources=['src/config/resource_path.c','src/config/resource_path_shared.c','src/config/resource_path.h','standalone/resource_path_pair.c','standalone/resource_path_host.c','standalone/test_resource_path_pair.py','standalone/build_context_help.py','standalone/build_path_session.py']
 frozen={n:sha(ROOT/n) for n in sources};flags=['-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc']
 for name,path,extra in [('control','src/config/resource_path.c',['-dresource_pcplus_path=control_pcplus','-dresource_program_path=control_program']),('shared','src/config/resource_path_shared.c',[])]:
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(out/(name+'.obj')),str(ROOT/path)],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fe=RPAIR.EXE',str(ROOT/'standalone/resource_path_pair.c'),str(out/'control.obj'),str(out/'shared.obj')],cwd=out,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-i='+str(ROOT/'src/config'),'-fe=RBASE.EXE',str(ROOT/'standalone/resource_path_host.c'),str(out/'shared.obj')],cwd=out,check=True)
 (out/'RUN.BAT').write_bytes(b'@echo off\r\nRPAIR >PAIR.TXT\r\nif errorlevel 1 goto bad\r\nRBASE >BASE.TXT\r\nif errorlevel 1 goto bad\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:bad\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n')
 (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[autoexec]
mount c "{out}"
c:
RUN.BAT
exit
''')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 pair=(out/'PAIR.TXT').read_text();base=(out/'BASE.TXT').read_text() if (out/'BASE.TXT').exists() else ''
 match=re.fullmatch(r'RESOURCEPAIR cases=(\d+) failures=0\s*',pair)
 passed=bool(match) and (out/'RESULT.TXT').read_text().strip()=='PASS' and base.startswith('RESOURCE PATH PASS')
 report=dict(passed=passed,cases=int(match[1]) if match else None,base=base.strip(),sources=frozen,products={n:sha(out/n) for n in ['RPAIR.EXE','RBASE.EXE']},object_segments={n:object_segments(out/(n+'.obj')) for n in ['control','shared']},scope='Real DOS paired default/shared implementations with identical input/output pointers and guarded outputs. Synthetic PSP/MCB/environment within DOS-owned blocks; no real MCB mutation. Prefix/byte matrices, random envs, duplicates, invalid names and64KiB terminator boundaries, plus all preceding explicit argument/alias/extent assertions.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(pair.strip());print(base.strip());return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
