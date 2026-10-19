#!/usr/bin/env python3
"""Bind current native/compiler/transport/parent and actual DOS BREAK proofs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def load(name):return json.loads((ROOT/name).read_text())
def main():
 parent=sha('build/terminal/TERMINAL.EXE');child=sha('build/aspect-runner/ASPECT.EXE');serial=sha('build/aspect-serial/SERIAL.EXE')
 reports={}
 def evidence(name,binary=None):
  result=load(name);assert result['passed'],name
  if binary:assert result['binary_sha256']==binary,name
  reports[name]=dict(sha256=sha(name),result=result);return result
 for folder,binary in [('terminal',parent),('aspect-runner',child),('aspect-serial',serial)]:
  manifest=load(f'build/{folder}/manifest.json');assert manifest['binary_sha256']==binary
  for source,expected in manifest['sources'].items():assert sha(source)==expected,source
 c=evidence('build/aspect-break-compiler/checks.json');assert c['compiler_sha256']==sha('src/aspect/compiler.py')
 assert c['counts']==dict(accepted=64,presentation=64,rejected=143,unsupported=0,novel=19)
 for folder,count,instructions in [('aspect-break-native',2585,104),('aspect-fetch-native',2399,45)]:
  n=evidence(f'build/{folder}/checks.json');assert n['cases']==count and n['instruction_addresses']==n['all_native_instructions']==instructions
  assert n['manifest_sha256']==sha(f'build/{folder}/manifest.json')
  for source,expected in load(f'build/{folder}/manifest.json')['sources'].items():assert sha(source)==expected,source
 r=evidence('build/aspect-runtime/checks.json',sha('build/aspect-runtime/EXECUTE.EXE'))
 assert r['DOS_summary']=='ASPECT_RUNTIME 1147 cases 26330 checks 0 failures'
 assert r['supported_slot_count']==71 and r['unsupported_slot_cases']==144
 assert len(r['SET_family']['supported_subcommands'])==12 and r['SET_family']['unsupported_subcommands_tested']==244
 assert len(evidence('build/aspect-runner/break-policy-checks.json',child)['cases'])==11
 assert len(evidence('build/terminal/aspect-break-ui-checks.json',parent)['cases'])==10
 assert evidence('build/aspect-serial/break-owner-checks.json',serial)['inputs']==626
 assert len(evidence('build/aspect-runner/break-linked-checks.json',child)['cases'])==31
 assert evidence('build/aspect-render-client/checks.json',child)['inputs']==47
 assert len(evidence('build/terminal/aspect-render-parent-client-checks.json',parent)['cases'])==22
 assert len(evidence('build/aspect-render-client-dos/checks.json',child)['cases'])==5
 assert len(evidence('build/aspect-serial/dos-checks.json',serial)['cases'])==6
 assert evidence('build/aspect-serial/checks.json',serial)['inputs']==108
 assert evidence('build/aspect-runner/checks.json',child)['DOS_summary']=='RUNNER 21 cases 105 checks 0 failures'
 for folder,count in [('aspect-break-dos',5),('aspect-when-renderer-dos',8),('aspect-set-status-dos',6)]:
  path=f'build/{folder}/break-final/checks.json';result=evidence(path)
  assert result['terminal_sha256']==parent and result['runner_sha256']==child and len(result['cases'])==count
  assert all(case['passed'] and all(case['checks'].values()) for case in result['cases'])
  if folder=='aspect-break-dos':
   for case in result['cases']:
    screen=f'build/{folder}/break-final/{case["case"]}/SCREEN.BIN'
    assert b'*** BREAK ***' not in (ROOT/screen).read_bytes()[::2]
    case['recorded_post_return_notice_removed']=dict(passed=True,screen_sha256=sha(screen))
 proof=evidence('docs/validation/application-components-source-build.json')
 assert proof['output_count']==138 and all(o['matches_workspace'] for o in proof['outputs'].values())
 for name,binary in [('terminal/TERMINAL.EXE',parent),('aspect-runner/ASPECT.EXE',child),('aspect-serial/SERIAL.EXE',serial)]:assert proof['outputs'][name]['sha256']==binary
 for leaf,binary in [('TERMINAL.EXE',parent),('ASPECT.EXE',child)]:assert sha('build/dos-package/'+leaf)==binary
 bbs={}
 for name,label,cancelled in [('synchronet','break-final-sync','draft_aborted'),('enigma','break-final-enigma30','no_post_saved')]:
  path=f'build/bbs-lab/script-login/{label}/checks.json';result=load(path)
  assert result['passed'] and all(result['checks'].values()) and result['terminal_sha256']==parent and result['runner_sha256']==child
  editor=result['editor'];assert editor['passed'] and all(editor['checks'].values()) and editor['checks'][cancelled]
  assert all(editor['observed_key_wire'].values())
  bbs[name]=dict(report=path,sha256=sha(path),checks=result['checks'],editor_checks=editor['checks'],key_wire=editor['observed_key_wire'],packet_delay_ms=editor['modem_packet_delay_ms'])
 assert bbs['enigma']['packet_delay_ms']==30
 old='build/aspect-break-dos/break-live01/checks.json';failed=load(old)
 assert not failed['passed'] and not next(c for c in failed['cases'] if c['case']=='cancel30000')['checks']['pulse_released_after_assertion']
 corrected='build/aspect-break-dos/break-live02/checks.json';assert load(corrected)['passed']
 sources=['src/aspect/break_commands.asm','src/aspect/fetch_command.asm','src/aspect/break_cursor_read.asm','src/aspect/serial_runtime.c','src/aspect/serial_runtime.h','src/aspect/resident_render.c','src/aspect/resident_render.h','src/aspect/runtime_bridge.asm','src/aspect/runtime.c','src/terminal/script_break_ui.asm','src/terminal/aspect_renderer.asm','standalone/test_aspect_break_dos.py','standalone/record_aspect_break_runtime.py']
 record=dict(schema='aspect-break-runtime-v1',passed=True,original_inputs=[],terminal_sha256=parent,runner_sha256=child,serial_diagnostic_sha256=serial,compiler_sha256=sha('src/aspect/compiler.py'),sources={name:sha(name) for name in sources},reports=reports,bbs=bbs,
  retained_observer_failure=dict(report=old,sha256=sha(old),reason='INT1C sampler stopped at child exit before post-cancel clear tick; independent hardware restoration passed. Corrected sampler continues across return.',corrected_report=corrected,corrected_sha256=sha(corrected)),
  limitations=['DOSBox-X virtual UART timing and controlled modeled IO are not physical modem validation.','Diagnostic BREAK tests model readiness only; actual pulses are established by separate parent/child DOS cases.','ENiGMA network-profile30ms-buffered regression does not resolve immediate-forwarding Home/Insert interaction failures.','CHAIN, complete scripts/recorder and all sixteen whole-application gates remain open.','Per-test manifest/map hashes are retained as recorded; byte-identical rebuilds can change map timestamps. Current source manifests and independent rebuild bind the final binaries separately.'])
 (ROOT/'docs/validation/aspect-break-runtime.json').write_text(json.dumps(record,indent=2)+'\n')
 print('BREAK runtime evidence:',len(reports),'reports;138 reproduced outputs')
if __name__=='__main__':main()
