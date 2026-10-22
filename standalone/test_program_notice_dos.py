#!/usr/bin/env python3
"""Run reconstructed notices with real DOS seconds, BIOS keys and screen copies."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/program-notice';manifest=json.loads((base/'manifest.json').read_text())
    assert manifest['original_inputs']==[] and manifest['products']['NOTICE.EXE']==sha(base/'NOTICE.EXE')
    assert all(sha(ROOT/name)==digest for name,digest in manifest['sources'].items())
    shutil.copy2(base/'NOTICE.EXE',out/'NOTICE.EXE')
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
NOTICE >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
    checks=dict(emulator_exit=process.returncode==0,DOS_exit=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),actual_six_cases=(out/'OUTPUT.TXT').read_bytes()==b'NOTICE 6 cases passed\r\n',binary_unchanged=sha(out/'NOTICE.EXE')==manifest['products']['NOTICE.EXE'])
    result=dict(passed=all(checks.values()),cases=6,checks=checks,manifest_sha256=sha(base/'manifest.json'),inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/program_notice_diagnostic.asm']},captures_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope=__doc__+' Three native entries crossed with queued-key or three-second-change completion under 8086 DOSBox-X. Screen save/draw/restore is an explicit source-owned whole-screen test platform; sound is a no-op boundary. Native original macro keyboard/window heap, foreground UART service, real PROGRAM and physical hardware are unverified.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks)));assert result['passed']
if __name__=='__main__':main()
