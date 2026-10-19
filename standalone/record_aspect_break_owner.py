#!/usr/bin/env python3
"""Freeze scoped BREAK compiler/native/transport evidence for public review."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def main():
 reports={}
 def evidence(name):
  result=json.loads((ROOT/name).read_text());assert result['passed'],name
  reports[name]=dict(sha256=sha(name),result=result);return result
 child=sha('build/aspect-runner/ASPECT.EXE');serial=sha('build/aspect-serial/SERIAL.EXE')
 for folder,binary in [('aspect-runner',child),('aspect-serial',serial)]:
  m=json.loads((ROOT/f'build/{folder}/manifest.json').read_text())
  assert m['binary_sha256']==binary
  for source,digest in m['sources'].items():assert sha(source)==digest,source
 c=evidence('build/aspect-break-compiler/checks.json')
 assert c['compiler_sha256']==sha('src/aspect/compiler.py')
 n=evidence('build/aspect-break-native/checks.json')
 assert n['cases']==2585 and n['instruction_addresses']==n['all_native_instructions']==104
 assert n['manifest_sha256']==sha('build/aspect-break-native/manifest.json')
 for source,digest in json.loads((ROOT/'build/aspect-break-native/manifest.json').read_text())['sources'].items():assert sha(source)==digest,source
 o=evidence('build/aspect-serial/break-owner-checks.json');assert o['binary_sha256']==serial and o['inputs']==626
 l=evidence('build/aspect-runner/break-linked-checks.json');assert l['binary_sha256']==child and len(l['cases'])==31
 for path,binary in [('build/aspect-serial/checks.json',serial),('build/aspect-serial/dos-checks.json',serial),('build/aspect-render-client/checks.json',child),('build/aspect-runner/txpace-linked-checks.json',child)]:
  assert evidence(path)['binary_sha256']==binary
 r=evidence('build/aspect-runtime/checks.json')
 assert r['DOS_summary']=='ASPECT_RUNTIME 878 cases 20586 checks 0 failures'
 assert r['binary_sha256']==sha('build/aspect-runtime/EXECUTE.EXE')
 proof=json.loads((ROOT/'build/application-source-proof/result.json').read_text())['application']
 assert proof['passed'] and proof['output_count']==132
 for name,expected in [('aspect-runner/ASPECT.EXE',child),('aspect-serial/SERIAL.EXE',serial)]:
  assert proof['outputs'][name]['sha256']==expected
 reports['build/application-source-proof/result.json']=dict(sha256=sha('build/application-source-proof/result.json'),output_count=132,source_snapshot_sha256=proof['source_snapshot_sha256'])
 bbs={}
 for name,label,cancelled in [('synchronet','break-416c-sync','draft_aborted'),('enigma','break-416c-enigma-network30','no_post_saved')]:
  path=f'build/bbs-lab/script-login/{label}/checks.json'
  result=json.loads((ROOT/path).read_text());assert result['passed'] and all(result['checks'].values())
  assert result['runner_sha256']==child and result['terminal_sha256']==sha('build/terminal/TERMINAL.EXE')
  editor=result['editor'];assert editor['passed'] and all(editor['checks'].values())
  assert editor['checks'][cancelled] and all(editor['observed_key_wire'].values())
  bbs[name]=dict(report=path,sha256=sha(path),checks=result['checks'],editor_checks=editor['checks'],
   key_wire=editor['observed_key_wire'],packet_delay_ms=editor['modem_packet_delay_ms'])
 assert bbs['enigma']['packet_delay_ms']==30
 failed_path='build/bbs-lab/script-login/break-416c-enigma30/checks.json'
 failed=json.loads((ROOT/failed_path).read_text())
 assert not failed['passed'] and failed['keyboard_profile']=='enigma-editor'
 assert failed['checks']['current_runner'] and failed['runner_sha256']==child
 assert not failed['editor']['checks']['home_moves_before_marker']
 assert not failed['editor']['checks']['insert_toggled_overtype']
 bbs['enigma_alternate_profile_failure']=dict(report=failed_path,sha256=sha(failed_path),
  passed=False,keyboard_profile='enigma-editor',packet_delay_ms=30,
  checks=failed['checks'],editor_checks=failed['editor']['checks'],
  scope='Additional alternate-profile attempt; retained failure, not the established network-profile regression.')
 for leaf,digest in [('TERMINAL.EXE',sha('build/terminal/TERMINAL.EXE')),('ASPECT.EXE',child)]:
  assert sha('build/dos-package/'+leaf)==digest
 result=dict(passed=True,scope='Preparatory native BREAK recovery, compiler grammar and maintained child transport owner. Not interpreter command or parent/UI integration.',
  child_sha256=child,serial_diagnostic_sha256=serial,parent_sha256=sha('build/terminal/TERMINAL.EXE'),
  compiler_sha256=sha('src/aspect/compiler.py'),reports=reports,bbs=bbs,
  incomplete=['BREAK0D and SET09/FETCH37/09 production interpreter dispatch','Parent configuration duration inheritance and explicit ABI lifetime','Native BREAK notice/status integration','Actual DOS BREAK pulse scheduling and physical UART/modem timing','ENiGMA immediate-forwarding Home/Insert interaction issue remains open','All sixteen full-application gates remain open'])
 (ROOT/'docs/validation/aspect-break-owner.json').write_text(json.dumps(result,indent=2)+'\n')
 print('BREAK evidence frozen:',len(reports),'reports;132 reproduced outputs')
if __name__=='__main__':main()
