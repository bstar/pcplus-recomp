#!/usr/bin/env python3
"""Bind the compiled EXECUTE checkpoint without closing full-application gates."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text())
def main():
 reports={}
 def evidence(path):
  data=read(path);assert data['passed'],path
  reports[path]=dict(sha256=sha(path),report=data)
  return data
 parent=sha('build/terminal/TERMINAL.EXE');child=sha('build/aspect-runner/ASPECT.EXE')
 manifest=read('build/aspect-runner/manifest.json');assert manifest['binary_sha256']==child
 for path,digest in manifest['sources'].items():assert sha(path)==digest,path
 for folder,count in [('aspect-chain-native',208),('aspect-end-wait-native',221)]:
  report=evidence(f'build/{folder}/checks.json');assert report['cases']==count
  mp=f'build/{folder}/manifest.json';assert report['manifest_sha256']==sha(mp)
  for path,digest in read(mp)['sources'].items():assert sha(path)==digest,path
 compiler=evidence('build/aspect-chain-compiler/checks.json')
 assert compiler['compiler_sha256']==sha('src/aspect/compiler.py')
 assert compiler['fixture_sha256']==sha('standalone/fixtures/aspect_chain_compiler_vectors.json')
 assert compiler['counts']==dict(accepted=35,rejected=41,presentation=35,rejected_variants=41,novel=7)
 path=evidence('build/aspect-script-path/checks.json');assert path['cases']==35 and path['checks']==141
 for source,digest in path['sources'].items():assert sha(source)==digest,source
 runtime=evidence('build/aspect-runtime/checks.json')
 assert runtime['supported_slot_count']==72 and runtime['unsupported_slot_cases']==143
 assert runtime['binary_sha256']==sha('build/aspect-runtime/EXECUTE.EXE')
 assert runtime['manifest_sha256']==sha('build/aspect-runtime/manifest.json')
 assert runtime['DOS_summary']=='ASPECT_RUNTIME 1146 cases 26309 checks 0 failures'
 chain=evidence('build/aspect-chain-runtime/checks.json')
 assert chain['DOS_summary']=='CHAIN 16 cases 287 checks 0 failures'
 assert chain['runtime_manifest_sha256']==runtime['manifest_sha256']
 serial=evidence('build/aspect-chain-serial-dos/checks.json');assert serial['runner_sha256']==child
 assert len(serial['cases'])==2 and all(all(c['checks'].values()) for c in serial['cases'])
 assert serial['reused_checker_sha256']==sha('standalone/test_aspect_script_serial_dos.py')
 runner=evidence('build/aspect-runner/checks.json');assert runner['binary_sha256']==child
 assert runner['DOS_summary']=='RUNNER 21 cases 105 checks 0 failures'
 for folder,count in [('aspect-chain-status-dos',1),('aspect-set-status-dos',6)]:
  result=evidence(f'build/{folder}/chain-final/checks.json')
  assert result['terminal_sha256']==parent and result['runner_sha256']==child
  assert len(result['cases'])==count and all(all(c['checks'].values()) for c in result['cases'])
 proof=evidence('docs/validation/application-components-source-build.json')
 assert proof['output_count']==149 and all(o['matches_workspace'] for o in proof['outputs'].values())
 for path in ['terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-runtime/EXECUTE.EXE']:
  assert proof['outputs'][path]['sha256']==sha('build/'+path),path
 for leaf,digest in [('TERMINAL.EXE',parent),('ASPECT.EXE',child)]:assert sha('build/dos-package/'+leaf)==digest
 bbs={}
 for name,label,check in [('synchronet','chain-final-sync','draft_aborted'),('enigma','chain-final-enigma30','no_post_saved')]:
  path=f'build/bbs-lab/script-login/{label}/checks.json';result=evidence(path)
  assert result['terminal_sha256']==parent and result['runner_sha256']==child
  assert all(result['checks'].values()) and result['editor']['passed'] and result['editor']['checks'][check]
  bbs[name]=dict(label=label,modem_buffer_ms=30 if name=='enigma' else 0,passed=True)
 result=dict(passed=True,terminal_sha256=parent,runner_sha256=child,
  compiler_sha256=sha('src/aspect/compiler.py'),recorder_sha256=sha('standalone/record_aspect_chain_runtime.py'),
  runner_manifest_sha256=sha('build/aspect-runner/manifest.json'),reports=reports,BBS=bbs,
  supported_opcode_slots=72,unsupported_opcode_slots=143,whole_application_gates_closed=[],
  limitations=['DOS ASP compiler and missing-ASX source fallback remain required.',
   'Parent status still shows the initial invocation filename after EXECUTE.',
   'Raw ASIO and diagnostic transport skip native terminal end-drain; attached drain uses maintained budget/cancel and BIOS-key policies.',
   'ENiGMA stock immediate forwarding remains unresolved; retained network-profile test uses explicit30ms buffering.',
   'Other command families, full UI/emulations/protocols/Host and physical Wi-Fi modems remain required.'])
 (ROOT/'docs/validation/aspect-chain-runtime.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded',len(reports),'reports;72 supported opcode slots; no full-application gate closed')
if __name__=='__main__':main()
