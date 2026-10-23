#!/usr/bin/env python3
"""Execute the banked native notice-input diagnostic in actual8086 DOS."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_native_mouse import ROOT,sha
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/notice-input';m=json.loads((base/'manifest.json').read_text());assert not m['original_inputs']
    assert sha(base/'NINPUT.EXE')==m['binary_sha256']
    for n,h in m['sources'].items():
        assert sha(ROOT/n)==h;target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    shutil.copyfile(base/'NINPUT.EXE',out/'NINPUT.EXE')
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
NINPUT >OUTPUT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
exit
:fail
echo FAIL>FAIL.TXT
exit
'''
    (out/'dosbox.conf').write_text(cfg)
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
    raw=(out/'OUTPUT.TXT').read_bytes() if (out/'OUTPUT.TXT').exists() else b''
    summary=re.fullmatch(rb'NINPUT checks=(\d+) failures=0 driver_bytes=(\d+)\r\n',raw)
    checks=dict(emulator_exit=r.returncode==0,DOS_pass=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        self_checks=bool(summary) and int(summary[1])>=50 and 0<int(summary[2])<65504,
        binary_unchanged=sha(out/'NINPUT.EXE')==m['binary_sha256'],sources_unchanged=all(sha(ROOT/n)==h for n,h in m['sources'].items()))
    result=dict(passed=all(checks.values()),checks=checks,self_checks=int(summary[1]) if summary else None,driver_bytes=int(summary[2]) if summary else None,
        binary_sha256=m['binary_sha256'],manifest_sha256=sha(base/'manifest.json'),checker_sha256=sha(Path(__file__)),
        captures_sha256={x.name:sha(x) for x in out.iterdir() if x.is_file()},sources=m['sources'],
        scope=__doc__+' Real native callback on foreign DS/SS, mouse repetition priority, distinct peek/read words, BIOS normalization/typeahead, timed idle, outer longjmp unwind and vector quarantine/repair with exact opaque driver/native-state restoration. Component only; no attached ASPECT, debug UI, KEY macro, physical clicks or full application acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('sources','captures_sha256')}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
