#!/usr/bin/env python3
"""Record current DOS carrier retry and a separate clean-source/fault proof."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('carrier-label','relay-label','source-label','unwind-label','break-label'):p.add_argument('--'+n,required=True)
 p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 candidate=a.candidate.resolve();target=a.output.resolve();assert candidate.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 for key,value in vars(a).items():
  if key.endswith('_label'):assert re.fullmatch(r'[A-Za-z0-9_-]+',value)
 out=ROOT/'build/bbs-lab/results/enigma'/a.carrier_label;r=load(out/'carrier-checks.json');negative=load(out/'carrier-current-audit-negative-checks.json')
 assert r['passed'] and all(r['checks'].values()) and not r['errors']
 assert negative['passed'] and len(negative['cases'])==13 and all(c['rejected'] for c in negative['cases'])
 for field,path in [('checker_sha256','lab/bbs/check_enigma_carrier_current_audit.py'),('positive_oracle_sha256','lab/bbs/check_enigma_carrier_audit.py'),('auditor_sha256','lab/bbs/audit_zmodem.py')]:assert negative[field]==sha(ROOT/path)
 for n,h in negative['capture_hashes'].items():assert sha(out/n)==h,n
 fixture=load(candidate/'search-instance.json');metadata=load(candidate/'instance.json')
 inputs={n:candidate/n for n in {**fixture['fixture_inputs'],**fixture['source_modules']}}
 for n in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE'):
  inputs[n]=ROOT/'build'/n;inputs['staged/'+Path(n).name]=out/'program'/Path(n).name
 named={'login':out/'program/LOGON.ASP','runner':ROOT/'lab/bbs/enigma_carrier_dos.py','relay':ROOT/'lab/bbs/carrier_relay.py','observer':ROOT/'lab/bbs/carrier_notice_watch.py','observer_base':ROOT/'lab/bbs/zmodem_label_watch.py','sampler_base':ROOT/'standalone/test_terminal.py','auditor':ROOT/'lab/bbs/audit_zmodem.py','modem_codec':ROOT/'lab/bbs/modem.py'}
 inputs.update(named);assert {n:sha(p) for n,p in inputs.items()}==r['input_hashes']
 archive=fixture['archives'][1];source=candidate/'file_base/pcplus_games'/archive['name'];assert sha(source)==archive['sha256']
 assert (out/'RECV').is_dir() and len(list((out/'RECV').iterdir()))==1
 assert next((out/'RECV').iterdir()).read_bytes()==source.read_bytes()
 assert r['snapshots'][1]['files']==[] and r['checks']['actual_carrier_loss_notice'] and r['checks']['confirmed_finish_notice']
 sessions=[load(out/f'connection-{i}/session.json') for i in (1,2)]
 assert all(s['done'] and not s['errors'] for s in sessions) and sessions[0]['interrupted'] and not sessions[1]['interrupted']
 relay_path=ROOT/'build/bbs-lab/carrier-relay'/a.relay_label/'checks.json';relay=load(relay_path);assert relay['passed'] and all(relay['checks'].values())
 for n,h in relay['sources'].items():assert sha(ROOT/n)==h,n
 proof_folder=ROOT/'build/aspect-unwind-mouse/source-proofs'/a.source_label;proof=load(proof_folder/'result.json')
 assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==31
 assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_unwind_source.py') and proof['log_sha256']==sha(proof_folder/'build.log')
 for n,h in proof['sources'].items():assert sha(ROOT/n)==sha(proof_folder/'source'/n)==h,n
 for n,p in proof['products'].items():assert p['expected']==p['actual']==sha(ROOT/'build'/n)==sha(proof_folder/'source/build'/n),n
 assert proof['products']['terminal/TERMINAL.EXE']['actual']==r['terminal_sha256']
 assert proof['products']['aspect-runner/ASPECT.EXE']['actual']==r['input_hashes']['aspect-runner/ASPECT.EXE']
 assert proof['products']['aspect-compiler-dos/ASPCOMP.EXE']['actual']==r['input_hashes']['aspect-compiler-dos/ASPCOMP.EXE']
 captures={str(relay_path.relative_to(ROOT)):sha(relay_path),str((proof_folder/'result.json').relative_to(ROOT)):sha(proof_folder/'result.json'),str((proof_folder/'build.log').relative_to(ROOT)):sha(proof_folder/'build.log')}
 source_target={}
 for label,passed in [('before',False),('after',True)]:
  folder=ROOT/'build/bbs-lab'/('current-mouse-source-target-'+label+'-01');m=load(folder/'result.json')
  assert m['passed']==passed and sha(folder/'make.log')==m['log_sha256']
  if passed:assert Path(m['source_proof']).resolve()==proof_folder.resolve() and m['exit_code']==0
  else:
   assert m['exit_code']!=0
   failures=re.findall(r'Fresh unwind source: 0 products FAIL (.+)',(folder/'make.log').read_text());assert len(failures)==1
   failed=Path(failures[0]);failure_proof=load(failed/'result.json');assert not failure_proof['passed'] and 'standalone/aspect_process_diagnostic.c' not in failure_proof['sources']
   assert "Unable to open" in (failed/'build.log').read_text()
   for p in (failed/'result.json',failed/'build.log'):captures[str(p.relative_to(ROOT))]=sha(p)
  source_target[label]=m
  for p in (folder/'result.json',folder/'make.log'):captures[str(p.relative_to(ROOT))]=sha(p)
 fault_results={}
 for name,folder,expected in [('ordinary',ROOT/'build/aspect-unwind/runs'/a.unwind_label,17),('break_owner',ROOT/'build/aspect-unwind-break/runs'/a.break_label,5)]:
  d=load(folder/'result.json');assert d['passed'] and len(d['cases'])==expected and all(c['passed'] and all(c['checks'].values()) for c in d['cases'])
  for n,h in d['sources'].items():assert sha(ROOT/n)==h,n
  assert d['parent_sha256']==sha(ROOT/'build/terminal-process/TERMINAL.EXE')
  assert d['child_sha256']==sha(ROOT/('build/aspect-fault-break/ASPECT.EXE' if name=='break_owner' else 'build/aspect-fault/ASPECT.EXE'))
  fault_results[name]=dict(cases=expected,parent_sha256=d['parent_sha256'],child_sha256=d['child_sha256'])
  for p in folder.rglob('*'):
   if p.is_file():captures[str(p.relative_to(ROOT))]=sha(p)
 for p in out.rglob('*'):
  if p.is_file():captures[str(p.relative_to(ROOT))]=sha(p)
 old=ROOT/'build/bbs-lab/aspect-fault-overflow-before-01/failure.json';failure=load(old);assert not failure['passed'] and failure['overflow_bytes']==5
 assert sha(old.parent/'ASPECT.map')==failure['map_sha256'] and sha(old.parent/'aspect_fault_driver.c')==failure['driver_sha256']
 listing=(ROOT/'build/aspect-fault/ASPECT.map').read_text();match=re.search(r'^_TEXT\s+CODE\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert match
 end=int(match[2],16)+int(match[3],16);assert end<=65536
 captures[str(old.relative_to(ROOT))]=sha(old);captures[str((old.parent/'ASPECT.map').relative_to(ROOT))]=sha(old.parent/'ASPECT.map')
 source_paths=['standalone/record_current_carrier.py','standalone/aspect_fault_driver.c','standalone/check_aspect_unwind_source.py','standalone/test_aspect_unwind_dos.py','lab/bbs/check_enigma_carrier_current_audit.py','lab/bbs/check_enigma_carrier_audit.py','lab/bbs/audit_zmodem.py','lab/bbs/enigma_carrier_dos.py','lab/bbs/carrier_relay.py','nix/flake.nix','nix/flake.lock','tools/dev','tools/bbs-dev','Makefile']
 result=dict(passed=True,current_DOS_carrier_retry_accepted=True,current_build_source_proof_accepted=True,physical_carrier_accepted=False,SIP_audio_carrier_accepted=False,
  terminal_sha256=r['terminal_sha256'],carrier_checks=r['checks'],notices=r['notices'],snapshots=r['snapshots'],protocol=r['protocol'],server_source_revision=metadata['upstream_revision'],server_client_sha256=metadata['client_sha256'],server_key_stream_sha256=metadata['key_stream_sha256'],server_fixture_input_hashes={**fixture['fixture_inputs'],**fixture['source_modules']},
  relay_checks=relay['checks'],negative_cases=negative['cases'],mutated_NFO_titles=negative['mutated_NFO_titles'],mutated_NFO_body_lines=negative['mutated_NFO_body_lines'],
  source_products={n:d['actual'] for n,d in proof['products'].items()},original_build_inputs=[],source_files=len(proof['sources']),source_proof_target=source_target,fault_recovery=fault_results,
  fault_diagnostic_before_bytes=failure['code_segment_bytes'],fault_diagnostic_after_bytes=int(match[3],16),fault_diagnostic_code_end=end,
  inputs={n:sha(ROOT/n) for n in source_paths},capture_sha256=captures,recorder_sha256=sha(Path(__file__)),
  scope='Current source-built976 DOS terminal: deliberate first Telnet abort after real partial ZIP write drives built-in DOSBox modem DCD/carrier loss, same-process redial/source-built ASPECT login, exact ZIP/strict controls/NFO and cleanup.16 producer gates,13 capture counterexamples and5 relay gates pass. ENiGMA fixture has the declared patched keyboard parser and synthetic data.31 products rebuild byte-identically from declared source with originals/old objects/REA databases absent. Fault diagnostic replaces equivalent IRQ-number expressions with a constant vector table to fix5-byte code overflow;17 ordinary and5 break-owner actual DOS recovery/control cases pass. No physical modem, SIP/audio carrier-loss or F01-F16 completion claim.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,carrier_checks=len(r['checks']),negative_cases=len(negative['cases']),source_products=31,fault_cases=22,receipt=str(target))))

if __name__=='__main__':main()
