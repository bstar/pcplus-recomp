#!/usr/bin/env python3
"""Execute independent source-only clipboard core self-checks in real DOS."""
import hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/clipboard'
def main():
 run=OUT/'run'
 if run.exists():shutil.rmtree(run)
 run.mkdir();shutil.copy2(OUT/'CLIPCORE.EXE',run/'CLIPCORE.EXE')
 cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{run}"
c:
CLIPCORE > RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(cfg)
 with (OUT/'dosbox.log').open('w') as log:
  code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],cwd=OUT,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20).returncode
 raw=(run/'CHECKS.BIN').read_bytes();checks,failures=struct.unpack('<HH',raw)
 passed=code==0 and (run/'PASS.TXT').is_file() and not (run/'FAIL.TXT').exists() and b'CLIPBOARD PASS' in (run/'RESULT.TXT').read_bytes() and checks>=550 and failures==0
 sources=['src/clipboard/clipboard.c','src/clipboard/clipboard.h','standalone/clipboard_self_test.c','standalone/clipboard_host.asm','standalone/test_clipboard_dos.py']
 result=dict(passed=passed,binary_sha256=hashlib.sha256((OUT/'CLIPCORE.EXE').read_bytes()).hexdigest(),checks=checks,failures=failures,sample_hex=raw.hex(),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual8086 DOS execution of source-owned clipboard state/list/extraction/packet self-checks, including196-byte capacity, all256 separators, duplicate/edit/hole behavior and input/output guards. No live UI, UART, file lookup or transfer implementation.')
 (OUT/'dos-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert passed
if __name__=='__main__':main()
