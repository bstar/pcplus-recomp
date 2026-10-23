#!/usr/bin/env python3
"""Actual8086 DOS resource-backed help, scrolling/search and handle restoration."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    c=['src/help/view.c','src/help/resource.c','src/help/document.c','src/help/format.c']
    assembly=['src/help/view_cursor.asm','src/help/resource_io.asm','src/mouse/dos_memory.asm']
    names=c+assembly+['src/help/view.h','src/help/resource.h','src/help/document.h','src/help/format.h','standalone/help_resource_diagnostic.c','standalone/test_help_resource_dos.py','standalone/build_help_resource.py','resources/help/notice.json','src/redisplay/command_menu.c']
    sources={n:sha(ROOT/n) for n in names}
    for n in names:
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    stage=out/'source';objects=[]
    for name in assembly:
        obj=out/(Path(name).stem+'.obj');subprocess.run(['nasm','-fobj',*(['-D_TEXT=NOTICEINPUT_CODE','-DCODE=FARCODE'] if 'dos_memory' in name else []),str(stage/name),'-o',str(obj)],check=True);objects.append(str(obj))
    for name in c:
        obj=out/(Path(name).stem+'.obj');subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-dASPECT_HELP_RESOURCE','-nt=NOTICEINPUT_CODE','-nc=FARCODE','-fo='+str(obj),str(stage/name)],cwd=out,check=True);objects.append(str(obj))
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dASPECT_HELP_RESOURCE','-k8192','-fm=HRES.map','-fe=HRES.EXE',str(stage/'standalone/help_resource_diagnostic.c'),*objects],cwd=out,check=True)
    subprocess.run(['python3',str(stage/'standalone/build_help_resource.py'),'--output',str(stage/'build/LOCHELP.HLP')],cwd=stage,check=True);shutil.copyfile(stage/'build/LOCHELP.HLP',out/'LOCHELP.HLP')
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
HRES >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
''')
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
    raw=(out/'OUTPUT.TXT').read_bytes();m=re.fullmatch(rb'HELPRESOURCE checks=(\d+) failures=0\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),self_checks=bool(m) and int(m[1])>=35,resource_unchanged=sha(out/'LOCHELP.HLP')==sha(stage/'build/LOCHELP.HLP'),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()))
    result=dict(passed=all(checks.values()),checks=checks,self_checks=int(m[1]) if m else None,binary_sha256=sha(out/'HRES.EXE'),sources=sources,original_inputs=[],scope=__doc__+'26 authored topics, real DOS reads, sparse model separately checked, native VGA snapshot and exact PSP JFT restoration. Component only; attached serial/outer unwind and full application acceptance remain unverified.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['passed'],checks,raw);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
