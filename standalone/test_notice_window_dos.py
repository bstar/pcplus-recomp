#!/usr/bin/env python3
"""Run guarded native animated windows with actual DOS far heap and VGA text RAM."""
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/notice-window';m=json.loads((base/'manifest.json').read_text());assert m['original_inputs']==[]
    assert all(sha(ROOT/path)==h for path,h in m['sources'].items()) and sha(base/'WINDOW.EXE')==m['products']['WINDOW.EXE'];shutil.copy2(base/'WINDOW.EXE',out/'WINDOW.EXE')
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
WINDOW >OUTPUT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
exit
:failed
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(cfg)
    with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=90)
    text=(out/'OUTPUT.TXT').read_text() if (out/'OUTPUT.TXT').exists() else '';match=re.fullmatch(r'WINDOW PASS (\d+) checks 114 allocations 114 frees\s*',text)
    checks=dict(emulator_exit=r.returncode==0,DOS_exit=(out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists(),all_cases=bool(match),binary_unchanged=sha(out/'WINDOW.EXE')==m['products']['WINDOW.EXE'])
    result=dict(passed=all(checks.values()),checks=checks,assertions=int(match[1]) if match else None,inputs={str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__),base/'manifest.json']},captures_sha256={path.name:sha(path) for path in out.iterdir() if path.is_file()},scope=__doc__+' Six rectangles crossed with animation0/1, invalid admission, allocation denial before mutation, retained guard failure/repair, changed-row rejection/repair and100 repeated owned lifetimes. Mode3/80x25/page0 DOSBox-X; sound is disabled and reached sound dependencies fail visibly. No live UART, PROGRAM, physical adapter or full application claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks,output=text)));assert result['passed']
if __name__=='__main__':main()
