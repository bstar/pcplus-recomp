#!/usr/bin/env python3
"""Actual8086 DOS cross-EXEC proof of source-linked resident_bridge OMF."""
import json,os,shutil,struct,subprocess
from pathlib import Path
from build_aspect_resident_bridge import ROOT,OUT,sha

def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for n,d in manifest['binaries'].items():assert sha(OUT/n)==d
 for n,d in manifest['sources'].items():assert sha(ROOT/n)==d,('source changed',n)
 previous=list(OUT.glob('dos-run-*'));folder=OUT/f'dos-run-{len(previous)+1:03d}';folder.mkdir(exist_ok=False)
 for name in manifest['binaries']:shutil.copyfile(OUT/name,folder/name)
 shutil.copyfile(OUT/'manifest.json',folder/'manifest.json')
 for name in ['parent.asm','child.asm','bridge.lst','parent.map']:shutil.copyfile(OUT/name,folder/name)
 for name in ['resident_bridge.asm','resident_bridge.inc']:shutil.copyfile(ROOT/'src/aspect'/name,folder/name)
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
mount c "{folder}"
c:
PARENT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=25)
 raw=(folder/'PARENT.BIN').read_bytes() if (folder/'PARENT.BIN').exists() else b''
 words=struct.unpack('<27H',raw) if len(raw)==54 else []
 failure=(folder/'FAILURE.BIN').read_bytes() if (folder/'FAILURE.BIN').exists() else b''
 checks=dict(DOS_exit=run.returncode==0 and (folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),descriptor=len(words)==27,binary_identity=all(sha(folder/n)==d for n,d in manifest['binaries'].items()))
 if words:checks.update(parent_code_data_distinct=words[4]!=words[2],distinct_EXEC_PSP=words[1]!=words[5],current_PSP_child=words[17]==words[5],all40_child_cases=words[21]==40,
  body32_times_only_preguard_refuses=words[13]==32,all8_callbacks_and_refusals=words[14]==words[20]==8,no_ABI_FLAGS_context_failure=words[15]==0,
  parent_DS_SS_every_body=words[16]==32,all48_interrupts=words[18]==48,actual_timer_child_ISR_on_parent=words[19]>0,
  bounded_observed_stack=0<words[22]<2048,declared_2048_stack=words[24]-words[23]==2048,invalid_initializers_rejected=words[25]==11,deep_abort_no_fallthrough=words[26]==0)
 stack=(folder/'STACK.BIN').read_bytes() if (folder/'STACK.BIN').exists() else b''
 touched=2048-next((i for i,v in enumerate(stack) if v!=0xcc),2048)
 checks['stack_measurement_matches_snapshot']=len(stack)==2048 and bool(words) and touched==words[22]
 history=[]
 reasons={('1f57b41f956573a5e6451f4efea03076ed5c5bfce4931bb590f0019d2ead8cfb','fe63fd0281953368aa889566711cdbaeb7bfe7d632869dfe4f60afc60c76113b'):'Fixture DOSstartup SS differed from DGROUP; initializer correctly refused.',('b2583856c40c58da508220ff1073ddbeb0fd5ca504ab775a41e061f189df6266','fe63fd0281953368aa889566711cdbaeb7bfe7d632869dfe4f60afc60c76113b'):'Fixture stack group was not aligned; initializer correctly refused.',('6c4af206151619644f32deac1ae316d6918ac80f68436e6453e3dfc84d2979d9','fe63fd0281953368aa889566711cdbaeb7bfe7d632869dfe4f60afc60c76113b'):'Invalidated pass: fixture saved outerEXEC SP through DS instead of CS; parent returned on wrapped stack.',('b364abafdb07a7e74abdc6fe942fe0599da275756639ec9f68e952f89673de5b','fe63fd0281953368aa889566711cdbaeb7bfe7d632869dfe4f60afc60c76113b'):'Invalidated pass: same fixture outerEXEC SP anchoring bug; anomalous touched extent is not bridge usage.',('a7f7f712b7404511b258afada7f97307cad60101ba3a9ebf574de5e13170f781','17af0b3e971d7b22499671c1f4ed197084d1cf98e3bd82cf73411d7e1c063762'):'Fixture source adaptation failed to generate operation matrix after editing its search token; counts/ABI checks correctly failed.'}
 for prior in sorted(OUT.glob('dos-run-*/checks.json')):
  old=json.loads(prior.read_text());identity=(old['binaries']['PARENT.EXE'],old['binaries']['CHILD.COM'])
  history.append(dict(report=str(prior.relative_to(ROOT)),sha256=sha(prior),reported_passed=old['passed'],accepted=identity not in reasons and old['passed'],reason=reasons.get(identity,'Retained prior execution; compare its manifest and binary identities.')))
 report=dict(regression_history=history,observed_parent_stack_touched_bytes=touched,passed=all(checks.values()),checks=checks,descriptor_words=words,failure_words=list(struct.unpack('<'+'H'*(len(failure)//2),failure)),run_directory=str(folder.relative_to(ROOT)),
  checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),binaries=manifest['binaries'],original_inputs=[],scope='Actual source-linked8086MZ OMF parentDS!=CS with8192B stack/lower2048B service slice, EXECchildCOM with guarded1024B callback stack, typedCOM1LSR callback, reentry/deepabort/guard faults/invalidinit/disable. No renderer/ASIO/MCBadmission or physical UARTIRQ claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'checks-dos.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
