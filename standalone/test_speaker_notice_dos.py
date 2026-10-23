#!/usr/bin/env python3
"""Run optional serviced notice sound, unwind and foreign-owner retry in8086 DOS."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/speaker-notice';m=json.loads((base/'manifest.json').read_text());assert not m['original_inputs']
    assert all(sha(ROOT/n)==h for n,h in m['sources'].items());assert sha(base/'NSOUND.EXE')==m['binary_sha256']
    shutil.copyfile(base/'NSOUND.EXE',out/'NSOUND.EXE')
    cfg=f'''[sdl]
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
NSOUND >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(cfg)
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),notice_cases=(out/'OUTPUT.TXT').read_bytes()==b'SPEAKER NOTICE 49 checks passed\r\n',binary_unchanged=sha(out/'NSOUND.EXE')==m['binary_sha256'])
    result=dict(passed=all(checks.values()),checks=checks,manifest_sha256=sha(base/'manifest.json'),checker_sha256=sha(Path(__file__)),captures_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope=__doc__+' Real optional notice/speaker banks, normal tone completion, service error, outer C longjmp abandonment, foreign-owner retention and repair, configuration and legacy callback precedence. Mixer muted. No actual PROGRAM binding, middle-of-instruction fault or physical audio claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
