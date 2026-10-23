#!/usr/bin/env python3
"""Verify supported active PRM projection with real8086 DOS and an independent byte oracle."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    names=['src/config/'+n for n in ['prm_projection.c','prm_projection.h','terminal_import.c','terminal_import.h','modem_import.c','modem_import.h','transfer_import.c','transfer_import.h','prm_dos.c','prm_dos.h']]
    names+=['standalone/prm_projection_diagnostic.c','standalone/test_prm_projection_dos.py']
    sources={n:sha(ROOT/n) for n in names};stage=out/'source'
    for n in names:
        dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
    def compile(folder):
        folder.mkdir(exist_ok=True);objects=[]
        for n in names:
            if not n.endswith('.c'):continue
            obj=folder/(Path(n).stem+'.obj');objects.append(str(obj))
            subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-fo='+str(obj),str(stage/n)],cwd=folder,check=True)
        subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-k8192','-fm=PRMPROJ.map','-fe=PRMPROJ.EXE',*objects],cwd=folder,check=True)
    compile(out)
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
PRMPROJ >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
''')
    with (out/'dosbox.log').open('w') as log:
        run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    raw=(out/'OUTPUT.TXT').read_bytes();match=re.fullmatch(rb'PRMPROJECT checks=(\d+) failures=0\r\n',raw)
    baseline=bytearray((i*37+129)&255 for i in range(1264));baseline[0x31c]=0;baseline[0x42c:0x42e]=bytes.fromhex('efbe')
    expected=bytearray(baseline)
    # Independent expected native offsets/bytes, not the C emitter's tables.
    words={0:1,2:7,4:0,6:1,8:8,0x176:0x2f8,0x186:3,0x198:0,0x19a:1,
           0x194:6,0x19c:1,0x19e:1,0x1ae:7,0x1b0:15,0x1b2:3,0x1b4:0x70,
           0x1b6:1,0x1e0:2,0x4ea:13,0x1e4:12,0xa:60,0xc:10,0xe:1,0x10:1,
           0x14:0,0x16:0,0x1a4:65535}
    for at,value in words.items():struct.pack_into('<H',expected,at,value)
    expected[0x12]=27;expected[0x1e2]=ord('~')
    strings={0x18:b'ATZ^M',0x47:b'ATDT',0x60:b'^M',0x79:b'+++~ATH0^M',0x92:b'',0xab:b''}
    strings.update({0xc4+i*16:(b'CONNECT' if i==0 else b'NO CARRIER' if i==1 else b'') for i in range(11)})
    for at,value in strings.items():expected[at:at+len(value)+1]=value+b'\0'
    inactive_base=bytearray(baseline);inactive_base[0xa:0x174]=bytes([255])*(0x174-0xa)
    inactive=bytearray(inactive_base)
    for at,value in words.items():
        if at<0xa or at>=0x174:struct.pack_into('<H',inactive,at,350 if at==0x1a4 else value)
    inactive[0x1e2]=ord('~')
    checks=dict(emulator_exit=run.returncode==0,DOS_assertions=bool(match),DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        baseline_exact=(out/'BASE.BIN').read_bytes()==baseline,projection_exact=(out/'ACTIVE.BIN').read_bytes()==expected,
        inactive_baseline_exact=(out/'INBASE.BIN').read_bytes()==inactive_base,
        inactive_projection_exact=(out/'INACTIVE.BIN').read_bytes()==inactive,
        sources_current=all(sha(ROOT/n)==h==sha(stage/n) for n,h in sources.items()))
    compile(out/'rebuild');checks['fresh_link']=sha(out/'PRMPROJ.EXE')==sha(out/'rebuild/PRMPROJ.EXE')
    report=dict(passed=all(checks.values()),checks=checks,self_checks=int(match[1]) if match else None,sources=sources,
        original_inputs=[],binary_sha256=sha(out/'PRMPROJ.EXE'),projected_sha256=sha(out/'ACTIVE.BIN'),
        scope='Supported serial/modem/transfer fields over opaque PRM baseline, actual8086 DOS; optional inactive modem preserves private fields while projecting shared serial values and explicit current BREAK. Two exact1264-byte independent oracles and fresh-link reproduction. No directory metadata, sound/mouse/current attribute projection, register handback, helper routing, returned settings commit or hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],report
    print('PASS',report['self_checks'],'DOS checks and exact active image')
if __name__=='__main__':main()
