#!/usr/bin/env python3
"""Build the pure HOOK exchange codec in an empty tree and compare host/8086 DOS."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/process/hook_exchange.c','src/process/hook_exchange.h','standalone/hook_exchange_diagnostic.c','standalone/test_hook_exchange_dos.py']
    sources={n:sha(ROOT/n) for n in names};stage=out/'source'
    for n in names:
        target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    host=out/'host';host.mkdir()
    subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-o',str(host/'hookcheck'),str(stage/names[0]),str(stage/names[2])],check=True)
    h=subprocess.run([str(host/'hookcheck')],cwd=host,stdout=subprocess.PIPE,check=True);(out/'HOST.TXT').write_bytes(h.stdout)
    obj=out/'exchange.obj'
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-nt=HOOK_CODE','-nc=FARCODE','-fo='+str(obj),str(stage/names[0])],cwd=out,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=HKEXCH.map','-fe=HKEXCH.EXE',str(stage/names[2]),str(obj)],cwd=out,check=True)
    config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 3000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
HKEXCH >OUTPUT.TXT
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
    raw=(out/'OUTPUT.TXT').read_bytes();match=re.fullmatch(rb'HOOKEXCHANGE checks=(\d+) failures=0\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),DOS_assertions=bool(match),host_DOS_output=h.stdout.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),exchange_bytes=(host/'HOOK.BIN').read_bytes()==(out/'HOOK.BIN').read_bytes(),tail_bytes=(host/'TAIL.TXT').read_bytes()==(out/'TAIL.TXT').read_bytes(),sources_unchanged=all(sha(ROOT/n)==digest==sha(stage/n) for n,digest in sources.items()))
    # Independently construct expected raw frame from the authored diagnostic recipe.
    integers=bytes((i*17+128)&255 for i in range(20));text=bytearray(128+i%127 for i in range(810))
    for i in range(10):text[i*81+(80 if i==9 else i*8)]=0
    prm=bytes((i*37)&255 for i in range(1264))
    checks['expected_frame']=(out/'HOOK.BIN').read_bytes()==integers+text+prm
    checks['expected_tail']=(out/'TAIL.TXT').read_bytes()==(' PCPLUS '+str(0x1234d126)+' '+str(0x1234d13a)+' '+str(0x12341b84)+' 3').encode()
    rebuild=out/'rebuild';rebuild.mkdir()
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-nt=HOOK_CODE','-nc=FARCODE','-fo='+str(rebuild/'exchange.obj'),str(stage/names[0])],cwd=rebuild,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fe=HKEXCH.EXE',str(stage/names[2]),str(rebuild/'exchange.obj')],cwd=rebuild,check=True)
    checks['fresh_link']=sha(rebuild/'HKEXCH.EXE')==sha(out/'HKEXCH.EXE')
    result=dict(passed=all(checks.values()),checks=checks,self_checks=int(match[1]) if match else None,sources=sources,original_inputs=[],binary_sha256=sha(out/'HKEXCH.EXE'),scope='Fresh-source host/C89 and actual8086 DOS HOOK KEY argument codec and opaque2094-byte staging. No helper EXEC, foreign pointer dereference, PSP admission, memory ownership, UART or live settings commit. Native command prefix/order and bank shape are separate REA observations.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],result
    print('PASS',result['self_checks'],'host/DOS checks')
if __name__=='__main__':main()
