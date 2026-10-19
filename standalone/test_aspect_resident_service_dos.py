#!/usr/bin/env python3
"""Execute isolated far-service parent+child under actual8086 DOSBox-X."""
import hashlib,json,os,struct,subprocess
from pathlib import Path
from build_aspect_resident_service import ROOT,OUT,sha

def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for name,digest in manifest['binaries'].items():assert sha(OUT/name)==digest
 for name in ['PASS.TXT','FAIL.TXT','PARENT.BIN']:(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=dummy
[autoexec]
@echo off
mount c "{OUT}"
c:
PARENT >CONSOLE.TXT
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
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=25)
 payload=(OUT/'PARENT.BIN').read_bytes() if (OUT/'PARENT.BIN').exists() else b''
 words=struct.unpack('<23H',payload) if len(payload)==46 else []
 checks=dict(DOS_exit=run.returncode==0 and (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),descriptor=len(words)==23,
  binary_identity=all(sha(OUT/n)==d for n,d in manifest['binaries'].items()))
 if words:checks.update(magic=words[0]==0x5253,distinct_EXEC_PSP=words[1]!=words[5],child_remains_current_PSP=words[17]==words[5],idle_after_return=words[9]==0,
  all32_calls=words[13]==32,all32_depth_refusals=words[14]==32,no_ABI_flag_PSP_guard_failures=words[15]==0,
  parent_DS_SS_all_calls=words[16]==32,all96_injected_interrupts=words[18]==96,real_timer_ISR_on_parent_stack=words[19]>0,all32_callbacks=words[20]==32,all32_child_cases=words[21]==32,observed_stack_extent_bounded=0<words[22]<=1024)
 report=dict(passed=all(checks.values()),checks=checks,descriptor_words=words,checker_sha256=sha(Path(__file__)),observed_parent_stack_touched_bytes=words[22] if words else None,manifest_sha256=sha(OUT/'manifest.json'),binaries=manifest['binaries'],original_inputs=[],scope='Source-owned parent EXEC child, real8086 DOS,1024B stack slices,32B redzones,32calls IF0/1, nested child realCOM1 LSR callbacks/depth1 refusal, softwareINT60 and realINT1C child ISR on parent stack. No renderer/product ASIO integration, arbitrary reentrancy, NMIs or physical UART IRQ claim.')
 (OUT/'checks-dos.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
