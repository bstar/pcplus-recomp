#!/usr/bin/env python3
"""Run serviced composed native notices with actual DOS far heap and VGA text RAM."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--banked',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/('build/notice-bank' if a.banked else 'build/notice');m=json.loads((base/'manifest.json').read_text());assert m['original_inputs']==[]
    assert all(sha(ROOT/path)==h for path,h in m['sources'].items()) and sha(base/'NOTICE.EXE')==m['binary_sha256'];shutil.copy2(base/'NOTICE.EXE',out/'NOTICE.EXE')
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
NOTICE >OUTPUT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
exit
:failed
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(cfg)
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=90)
    text=(out/'OUTPUT.TXT').read_text() if (out/'OUTPUT.TXT').exists() else '';match=re.fullmatch(r'NOTICE PASS (\d+) checks (\d+) allocations (\d+) frees\s*',text)
    checks=dict(emulator_exit=r.returncode==0,DOS_exit=(out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),all_cases=bool(match) and match[2]==match[3],binary_unchanged=sha(out/'NOTICE.EXE')==m['binary_sha256'])
    result=dict(passed=all(checks.values()),checks=checks,assertions=int(match[1]) if match else None,inputs={str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),base/'manifest.json']},captures_sha256={path.name:sha(path) for path in out.iterdir() if path.is_file()},allocations=int(match[2]) if match else None,frees=int(match[3]) if match else None,scope=__doc__+' Actual native notice/window/text and BIOS keys/DOS clock; explicit frozen-DOS-clock INT21 observer proves real BIOS timeout and poll-budget cleanup; separate controlled tick fixtures exercise midnight wrap and invalid samples. Sound/service callbacks are diagnostic recording/failure boundaries. No actual UART, PROGRAM/shared parent integration or physical claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks,output=text)));assert result['passed']
if __name__=='__main__':main()
