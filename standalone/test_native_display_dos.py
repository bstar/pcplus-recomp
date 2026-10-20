#!/usr/bin/env python3
"""Run the native display component under actual8086 DOS and retain each attempt."""
import argparse,json,os,re,shutil,subprocess,uuid
from pathlib import Path
from build_native_display import ROOT,OUT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='run-'+uuid.uuid4().hex)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    run=OUT/'runs'/args.label;run.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((OUT/'manifest.json').read_text())
    for p,h in {**manifest['sources'],**manifest['process_sources']}.items():
        assert sha(ROOT/p)==h,p
        target=run/'sources'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,target)
    for name in ('DISPLAY.EXE','VIDEO.COM','manifest.json'):shutil.copyfile(OUT/name,run/name)
    (run/'PCPTEST.BAT').write_text('@echo off\nDISPLAY >CHECKS.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
    (run/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 3000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
mount c "{run}"
c:
PCPTEST.BAT
exit
''')
    timeout=False
    with (run/'dosbox.log').open('w') as log:
        try:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
        except subprocess.TimeoutExpired:timeout=True
    text=(run/'CHECKS.TXT').read_text() if (run/'CHECKS.TXT').exists() else ''
    match=re.search(r'DISPLAY (\d+) checks (\d+) failures',text)
    passed=not timeout and bool(match) and int(match[2])==0 and (run/'RESULT.TXT').read_text().strip()=='PASS'
    report=dict(passed=passed,timed_out=timeout,checks=int(match[1]) if match else 0,
        binary_sha256=sha(run/'DISPLAY.EXE'),manifest_sha256=sha(run/'manifest.json'),
        checker_sha256=sha(Path(__file__)),artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()},scope=manifest['scope'])
    (run/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(text.strip());print('PASS' if passed else 'FAIL');print(run)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
