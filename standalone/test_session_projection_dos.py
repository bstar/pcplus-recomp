#!/usr/bin/env python3
"""Run the production projection API after real startup in a diagnostic8086 terminal."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from check_setup_model import image
from directory_fixtures import directory
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-probe';m=json.loads((base/'manifest.json').read_text())
    assert m['session_projection_probe'] and sha(base/'TERMINAL.EXE')==m['binary_sha256']
    raw=bytearray(image());struct.pack_into('<HH',raw,0x4e4,8,4);raw=bytes(raw);cases=[]
    recipes=[('serial','@TEST.PRM 19200',False,None,5,4,350),
        ('MODEM','@TEST.PRM /D:CaseTest:23 38400',False,None,6,4,None),
        ('directory-MODEM','@TEST.PRM /E:TEST.DIR /N:1',False,0,6,6,None),
        ('directory-DIRECT','@TEST.PRM /E:TEST.DIR /N:1',True,1,6,6,None),
        ('serial-inactive','@TEST.PRM 19200',True,None,5,4,350)]
    for name,args,bad,direct,rate,profile,line_break in recipes:
        folder=out/name;folder.mkdir();source=bytearray(raw)
        if bad:source[0xa:0x174]=bytes([255])*(0x174-0xa)
        source=bytes(source)
        (folder/'TEST.PRM').write_bytes(source);(folder/'PBASE.BIN').write_bytes(source)
        if direct is not None:(folder/'TEST.DIR').write_bytes(directory(direct=direct))
        shutil.copyfile(base/'TERMINAL.EXE',folder/'TERMINAL.EXE')
        (folder/'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm','-fbin',str(folder/'sampler.asm'),'-o',str(folder/'SNAP.COM')],check=True)
        (folder/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount d "{folder}"
d:
SNAP B
TERMINAL {args}
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
SNAP A
exit
''')
        with (folder/'dosbox.log').open('w') as log:
            run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
        expected=bytearray(source);struct.pack_into('<H',expected,2,rate);struct.pack_into('<H',expected,0x194,profile)
        if line_break is not None:struct.pack_into('<H',expected,0x1a4,line_break)
        checks=dict(emulator_exit=run.returncode==0,DOS_pass=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),
            projection_status=(folder/'PSTAT.BIN').read_bytes()==b'\0\0',exact_image=(folder/'POUT.BIN').read_bytes()==expected,
            baseline_unchanged=(folder/'PBASE.BIN').read_bytes()==source,settings_unchanged=(folder/'TEST.PRM').read_bytes()==source,
            hardware_restored=(folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and len((folder/'BEFORE.BIN').read_bytes())==42,
            binary_unchanged=sha(folder/'TERMINAL.EXE')==m['binary_sha256'])
        r=dict(case=name,passed=all(checks.values()),checks=checks,arguments=args,inactive_private_invalid=bad,projection_sha256=sha(folder/'POUT.BIN'))
        (folder/'result.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'],r
        cases.append(r);print('PASS8086',name,flush=True)
    sources=dict(m['sources'])
    for n in ['standalone/test_session_projection_dos.py','standalone/check_setup_model.py','standalone/check_modem_import.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        dst=out/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
    result=dict(passed=True,cases=cases,sources=sources,binary_sha256=m['binary_sha256'],
        scope='Five actual8086 DOS runs of diagnostic source-built terminal: production startup/import/CLI/directory/capture/projection code, explicit probe before mouse/UART acquisition, exact1264-byte images and unchanged hardware/files. Not terminal HOOK execution, online serial continuity, returned settings commit or physical hardware acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five actual8086 terminal projection workflows')
if __name__=='__main__':main()
