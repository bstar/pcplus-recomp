#!/usr/bin/env python3
"""Fresh-source real DOS HOOK allocation, direct helper execution and retirement."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--production',action='store_true');a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/process/hook_owner.h','src/process/hook_owner.c','src/process/hook_owner_dos.asm','src/process/hook_exchange.h','src/process/hook_exchange.c','src/process/dos_exec.h','src/process/dos_exec.asm','standalone/hook_owner_diagnostic.c','standalone/hook_owner_child.c','standalone/hook_owner_support.asm','standalone/test_hook_owner_dos.py']
    sources={n:sha(ROOT/n) for n in names};stage=out/'source'
    for n in names:
        p=stage/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
    def compile(folder):
        objects=[]
        for name,flags in [('src/process/dos_exec.asm',['-DPROCESS_CODE_BANK']),('src/process/hook_owner_dos.asm',[] if a.production else ['-DHOOK_OWNER_DIAGNOSTIC'])]:
            obj=folder/(Path(name).stem+'.obj');subprocess.run(['nasm','-fobj',*flags,str(stage/name),'-o',str(obj)],check=True);objects.append(obj)
        for name in ['src/process/hook_exchange.c','src/process/hook_owner.c']:
            obj=folder/(Path(name).stem+'.obj');subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-nt=HOOK_CODE','-nc=FARCODE','-fo='+str(obj),str(stage/name)],cwd=folder,check=True);objects.append(obj)
        support=folder/'support.obj';subprocess.run(['nasm','-fobj',str(stage/'standalone/hook_owner_support.asm'),'-o',str(support)],check=True)
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=HOWNER.map','-fe=HOWNER.EXE',*([] if a.production else ['-dHOOK_OWNER_DIAGNOSTIC']),str(stage/'standalone/hook_owner_diagnostic.c'),*[str(o) for o in objects],str(support)],cwd=folder,check=True)
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=HOOKCH.map','-fe=HOOKCH.EXE',str(stage/'standalone/hook_owner_child.c'),str(folder/'hook_exchange.obj')],cwd=folder,check=True)
    compile(out)
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
c:
HOWNER >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    raw=(out/'OUTPUT.TXT').read_bytes();m=re.fullmatch(rb'HOOKOWNER checks=(\d+) failures=0 generation=(\d+)\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),DOS_assertions=bool(m),helper_capture=(out/'HCHILD.BIN').stat().st_size==2094 if (out/'HCHILD.BIN').exists() else False,sources_unchanged=all(sha(ROOT/n)==h==sha(stage/n) for n,h in sources.items()))
    if checks['helper_capture']:
        frame=(out/'HCHILD.BIN').read_bytes();expected_a=bytes(((128+i*17)&255)^0x3c for i in range(20));b=bytearray(128+i%127 for i in range(810))
        for i in range(10):b[i*81+i]=0
        b[0]=1;b[80]=0
        for i in range(10):b[i*81:i*81+3]=bytes([ord('H'),ord('0')+i,0])
        prm=bytes(((i*37)&255)^0x5a for i in range(1264));checks['exact_returned_frame']=frame==expected_a+b+prm
    rebuild=out/'rebuild';rebuild.mkdir();compile(rebuild)
    checks['fresh_parent_link']=sha(rebuild/'HOWNER.EXE')==sha(out/'HOWNER.EXE')
    checks['fresh_helper_link']=sha(rebuild/'HOOKCH.EXE')==sha(out/'HOOKCH.EXE')
    result=dict(production_backend=a.production,passed=all(checks.values()),checks=checks,self_checks=int(m[1]) if m else None,generations=int(m[2]) if m else None,sources=sources,original_inputs=[],binary_sha256=sha(out/'HOWNER.EXE'),helper_sha256=sha(out/'HOOKCH.EXE'),scope='Actual8086 DOS guarded far allocation, parent MCB/PSP ownership, direct source-built HOOK helper EXEC, malformed returned strings, damaged guards/MCB repair, missing helper, busy owner, injected resize/allocation/free errors, exact raw bank mutations, largest-free/JFT/vector restoration. Standalone foreground only; no terminal/UART/live PRM application or arbitrary asynchronous fault acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],result['checks']
    print('PASS',result['self_checks'],'DOS ownership checks')
if __name__=='__main__':main()
