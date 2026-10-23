#!/usr/bin/env python3
"""Real8086 DOS view ownership, snapshot restoration and selected repair paths."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/help/view.h','src/help/view.c','src/help/view_cursor.asm','src/help/notice_content.h','src/help/notice_content.c','src/mouse/dos_memory.asm','standalone/help_view_diagnostic.c','standalone/help_view_call_probe.asm','standalone/test_help_view_dos.py']
    sources={n:sha(ROOT/n) for n in names}
    for n in names:
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    objects=[]
    for name,flags in [('src/mouse/dos_memory.asm',['-D_TEXT=NOTICEINPUT_CODE','-DCODE=FARCODE']),('src/help/view_cursor.asm',[]),('standalone/help_view_call_probe.asm',[])]:
        obj=out/(Path(name).stem+'.obj');subprocess.run(['nasm','-fobj',*flags,str(out/'source'/name),'-o',str(obj)],check=True);objects.append(str(obj))
    for name in ['src/help/view.c','src/help/notice_content.c']:
        obj=out/(Path(name).stem+'.obj');subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dHELP_VIEW_DIAGNOSTIC','-nt=NOTICEINPUT_CODE','-nc=FARCODE','-fo='+str(obj),str(out/'source'/name)],cwd=out,check=True);objects.append(str(obj))
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dHELP_VIEW_DIAGNOSTIC','-k8192','-fe=HELPVIEW.EXE',str(out/'source/standalone/help_view_diagnostic.c'),*objects],cwd=out,check=True)
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
HELPVIEW >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
''')
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
    raw=(out/'OUTPUT.TXT').read_bytes();match=re.fullmatch(rb'HELPVIEW checks=(\d+) failures=0\r\n',raw)
    screen=(out/'HELP.BIN').read_bytes() if (out/'HELP.BIN').exists() else b''
    checks=dict(exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),self_checks=bool(match) and int(match[1])>=30,
        actual_screen=len(screen)==4000 and b'PCPlus // CONTEXT HELP' in screen[::2] and b'EXTERNAL PROGRAM / ERROR NOTICE' in screen[::2],sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()))
    report=dict(passed=all(checks.values()),checks=checks,self_checks=int(match[1]) if match else None,binary_sha256=sha(out/'HELPVIEW.EXE'),sources=sources,original_inputs=[],scope=__doc__+' Authored text/direct VGA, guarded DOS allocation; no attached notice/serial integration, arbitrary faults, original PCHELP UI or physical hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(report['passed'],checks,raw);return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
