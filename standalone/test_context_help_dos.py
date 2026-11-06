#!/usr/bin/env python3
"""Exercise the recovered help producer across real DOS EXEC, source inputs only."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build=a.build.resolve();run=a.output.resolve()
    run.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((build/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():
        assert sha(ROOT/name)==digest,name
        target=run/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    for name,digest in manifest['products'].items():
        assert sha(build/name)==digest,name
        shutil.copyfile(build/name,run/name)
    shutil.copyfile(build/'manifest.json',run/'manifest.json')
    shutil.copyfile(__file__,run/'checker.py')
    (run/'RUN.BAT').write_bytes(b'@echo off\r\nCONTEXT >CHECKS.TXT\r\nif errorlevel 1 goto bad\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:bad\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n')
    (run/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
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
RUN.BAT
exit
''')
    timed_out=False
    with (run/'dosbox.log').open('w') as log:
        try:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
        except subprocess.TimeoutExpired:timed_out=True
    output=(run/'CHECKS.TXT').read_text() if (run/'CHECKS.TXT').exists() else ''
    status=(run/'RESULT.TXT').read_text().strip() if (run/'RESULT.TXT').exists() else ''
    match=re.search(r'CONTEXT checks=(\d+) errors=(\d+) children=8 invalid=3',output)
    passed=not timed_out and status=='PASS' and bool(match) and int(match[2])==0
    report=dict(passed=passed,timed_out=timed_out,checks=int(match[1]) if match else 0,products=manifest['products'],manifest_sha256=sha(run/'manifest.json'),checker_sha256=sha(Path(__file__)),artifacts={x.name:sha(x) for x in run.iterdir() if x.is_file()},scope=manifest['scope'])
    (run/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(output.strip());print('PASS' if passed else 'FAIL');print(run)
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
