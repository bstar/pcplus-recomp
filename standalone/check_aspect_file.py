#!/usr/bin/env python3
"""Check real host/DOS file IO and linked native ASPECT flow; no originals."""
import json
import os
from pathlib import Path
import subprocess
from build_aspect_file import ROOT,OUT,sha


def main():
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_file.py')],check=True)
 host=OUT/'host';host.mkdir(exist_ok=True)
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-pedantic','-O2',
  '-I'+str(ROOT/'src/aspect'),str(ROOT/'src/aspect/file_io.c'),
  str(ROOT/'standalone/aspect_file_fixture.c'),'-o',str(host/'file-check')],check=True)
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 (host/'DONE.TXT').unlink(missing_ok=True)
 native_host=subprocess.run([str(host/'file-check')],cwd=host,check=True,capture_output=True,text=True,timeout=20)
 host_summary=(host/'DONE.TXT').read_text().strip();assert host_summary.endswith('0 failures')
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
FILE >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 dos_summary=(OUT/'DONE.TXT').read_text().strip()
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 assert dos_summary.endswith('0 failures'),dos_summary
 report=dict(passed=True,host_summary=host_summary,DOS_summary=dos_summary,
  binary_sha256=sha(OUT/'FILE.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
  check_sha256=sha(Path(__file__).resolve()),original_inputs=[],
  fixture_bytes=72016,host_fixture_sha256=sha(host/'FLOW.DAT'),DOS_fixture_sha256=sha(OUT/'FLOW.DAT'),
  scope='Same maintained file API uses real host and DOS stdio. DOS additionally runs recovered readers, DWORD seeks/calls, nested frames, returns and actual abort/longjmp. No opcode loop, parser or full script execution.')
 assert report['host_fixture_sha256']==report['DOS_fixture_sha256']
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
