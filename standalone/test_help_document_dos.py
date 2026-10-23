#!/usr/bin/env python3
"""Fresh-source host/8086 DOS incremental HLP reader and resumable search."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/help/format.h','src/help/format.c','src/help/document.h','src/help/document.c','standalone/help_document_diagnostic.c','standalone/test_help_document_dos.py','standalone/build_help_resource.py','resources/help/notice.json','src/redisplay/command_menu.c']
    sources={n:sha(ROOT/n) for n in names}
    for n in names:
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    stage=out/'source';objects=[]
    for name in ['src/help/format.c','src/help/document.c']:
        obj=out/(Path(name).stem+'.obj');subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-nt=HELPDOCUMENT_CODE','-nc=FARCODE','-fo='+str(obj),str(stage/name)],cwd=out,check=True);objects.append(str(obj))
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=HELPDOC.map','-fe=HELPDOC.EXE',str(stage/'standalone/help_document_diagnostic.c'),*objects],cwd=out,check=True)
    host=out/'host';host.mkdir()
    subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-o',str(host/'helpdoc'),*[str(stage/n) for n in ['src/help/format.c','src/help/document.c','standalone/help_document_diagnostic.c']]],check=True)
    h=subprocess.run([str(host/'helpdoc')],cwd=host,capture_output=True)
    (out/'HOST.TXT').write_bytes(h.stdout);assert h.returncode==0,h.stdout
    subprocess.run(['python3',str(stage/'standalone/build_help_resource.py'),'--output',str(stage/'build/LOCHELP.HLP')],cwd=stage,check=True)
    resource=json.loads((stage/'build/LOCHELP.json').read_text());assert resource['topics']==26 and not resource['original_inputs']
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
HELPDOC >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
''')
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
    raw=(out/'OUTPUT.TXT').read_bytes();m=re.fullmatch(rb'HELPDOC checks=(\d+) failures=0 max_read=(\d+)\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),self_checks=bool(m) and int(m[1])>=50 and int(m[2])<=80,
        host_DOS_results=h.stdout.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),fixture_bytes=(host/'DOCUMENT.HLP').read_bytes()==(out/'DOCUMENT.HLP').read_bytes(),sources_unchanged=all(sha(ROOT/n)==digest==sha(stage/n) for n,digest in sources.items()))
    result=dict(passed=all(checks.values()),checks=checks,self_checks=int(m[1]) if m else None,binary_sha256=sha(out/'HELPDOC.EXE'),sources=sources,resource=resource,original_inputs=[],scope=__doc__+' Real32-bit DOS seek beyond64KiB; one-record admission,80byte line steps, CP437/CRLF, wrapped title/body find-next and cancellation, malformed input and read faults. Authored26topic resource reuses existing menu prose. Component only; no integrated help view, serial-owner or full application acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['passed'],checks,raw);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
