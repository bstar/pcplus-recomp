#!/usr/bin/env python3
"""Bind current source/DOS/linked checks to the actual stock paced-host capture.

Run only after the separately observed full make command exits successfully.
This records component evidence; it cannot grant DOS/audio/BBS/hardware passes.
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import audit_batch,audit_controls,scan

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def current_inputs(result,key):
 for name,digest in result[key].items():assert sha(ROOT/name)==digest,name
def proof(path,key=None):
 r=read(path);assert r['passed'],path
 if key:current_inputs(r,key)
 return r
def summarize(path,result):
 return dict(result=str(path.relative_to(ROOT)),sha256=sha(path),case_count=result.get('case_count',result.get('DOS_cases',len(result.get('cases',[])))))

def verify_paced(path,library_sha256,bps,credit,flags,identity):
 r=proof(path);out=path.parent
 assert all(r['checks'].values()) and r['status']==r['helper_exit']==0
 assert r['source_bytes']==r['session_position']==r['session_bytes']==65797 and r['session_files']==1
 assert r['bps_ceiling']==bps and r['flags']==flags and r['credit']==credit
 assert not r['callback_errors'] and not r['verify_errors'] and r['error'] is None
 if identity:assert all(x['original_hex']==x['replacement_hex'] for x in r['offers'])
 else:
  for offer in r['offers']:
   original=list(scan(bytes.fromhex(offer['original_hex'])))
   replacement=list(scan(bytes.fromhex(offer['replacement_hex'])))
   assert len(original)==len(replacement)==1 and original[0]['type']==replacement[0]['type']==1
   assert original[0]['position']==(0x23000000|credit) and replacement[0]['position']==((flags<<24)|credit)
 for name,d in r['inputs'].items():assert sha(out/'frozen-source'/name)==d,name
 for name,d in r['captures_sha256'].items():assert sha(out/name)==d,name
 assert sha(out/'session.so')==r['library_sha256']==library_sha256
 assert sha(ROOT/'build/bbs-lab/enigma/helpers/sexyz')==r['helper_sha256']
 body=(out/'PCPRESS.BIN').read_bytes();assert len(body)==65797 and hashlib.sha256(body).hexdigest()==r['source_sha256']
 assert body==bytes((i*73+(i>>8)*19+37)&255 for i in range(65797))
 wire=(out/'sender.bin').read_bytes();response=(out/'receiver.bin').read_bytes()
 trace=[json.loads(line) for line in (out/'trace.jsonl').read_text().splitlines()]
 counts={'bbs':0,'dos':0}
 for row in trace:
  direction=row['direction'];assert row['offset']==counts[direction] and row['size']>0
  counts[direction]+=row['size']
 assert counts==dict(bbs=len(wire),dos=len(response))
 protocol=audit_batch(wire,{'PCPRESS.BIN':body})
 for file in protocol['files']:assert file.pop('source')==body
 protocol['controls']=audit_controls(protocol,response,trace,'bbs',max(row['seconds'] for row in trace)+1)
 assert json.loads(json.dumps(protocol))==r['protocol']
 return r,protocol

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--host',type=Path,required=True);p.add_argument('--linked',type=Path,required=True)
 p.add_argument('--paced',type=Path,required=True);p.add_argument('--regression-exit',type=Path,required=True)
 p.add_argument('--paced-conservative',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 host_path=a.host.resolve();linked_path=a.linked.resolve();paced_path=a.paced.resolve();exit_path=a.regression_exit.resolve();target=a.output.resolve();conservative_path=a.paced_conservative.resolve()
 assert all(q.is_relative_to(ROOT/'build') for q in (host_path,linked_path,paced_path,conservative_path,exit_path))
 assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 exit_record=read(exit_path);assert exit_record['exit_code']==0
 for name,digest in exit_record['logs'].items():assert sha(ROOT/name)==digest,name
 binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary);manifest_path=ROOT/'build/terminal/manifest.json';manifest=read(manifest_path)
 assert manifest['kind']=='source-only-interactive-dos-terminal' and manifest['binary_sha256']==digest
 current_inputs(manifest,'sources')
 assert all(not n.startswith(('analysis/','build/')) and (ROOT/n).resolve().is_relative_to(ROOT) and Path(n).suffix.lower() not in ('.exe','.bin','.img','.zip','.7z') for n in manifest['sources'])
 assert manifest['data_stack_bytes']==64896 and manifest['memory_layout']['near_bytes']==64896
 assert manifest['memory_layout']['far_pointer_relocations_verified']
 assert manifest['memory_layout']['resident_code_bytes']<65536
 host=proof(host_path,'inputs');assert host['case_count']==39 and host['baseline']['reproduced_status']==4
 baseline=host['baseline'];baseline_path=ROOT/baseline['proof'];assert sha(baseline_path)==baseline['proof_sha256']
 baseline_result=read(baseline_path);assert baseline_result['passed']
 assert sha(baseline_path.parent/'session.so')==baseline['library_sha256']
 for name,d in baseline_result['inputs'].items():assert sha(ROOT/baseline['frozen_source_root']/name)==d,name
 assert sha(host_path.parent/'session.so')==host['library_sha256']
 dos_path=ROOT/'build/zmodem-dos/checks.json';dos=proof(dos_path,'sources')
 assert dos['DOS_cases']==97 and dos['isolated_source_build_byte_identical'] and all(row['passed'] for row in dos['cases'])
 assert sha(dos_path.parent/'SESSION.EXE')==sha(dos_path.parent/'source-only/SESSION.EXE')==dos['binary_sha256']
 faults_path=ROOT/'build/download-compare/faults-01/result.json';faults=proof(faults_path,'inputs');assert faults['case_count']==64
 assert sha(faults_path.parent/'CHECK.EXE')==faults['binary_sha256']
 linked=proof(linked_path);assert linked['binary_sha256']==digest and linked['case_count']==14
 assert linked['test_sha256']==sha(ROOT/'standalone/check_terminal_zmodem_active_replay.py')
 assert all(row['passed'] and all(row['checks'].values()) for row in linked['cases'])
 regressions=[]
 for name,checker,count in [
  ('terminal-zmodem-live-checks.json','check_terminal_zmodem_live.py',78),
  ('terminal-zmodem-receive-credit-checks.json','check_terminal_zmodem_receive_credit.py',31),
  ('zmodem-upload-response-checks.json','check_zmodem_upload_timing.py',22),
  ('carrier-transfer-deadline-checks.json','check_carrier_transfer_deadline.py',4),
  ('zmodem-completed-replay-checks.json','check_zmodem_completed_replay.py',3),
  ('zmodem-cancel-checks.json','check_terminal_zmodem_cancel.py',5),
  ('zmodem-name-ui-checks.json','check_zmodem_name_ui.py',17)]:
  path=ROOT/'build/terminal'/name;r=proof(path)
  assert r['binary_sha256']==digest and len(r['cases'])==count,name
  assert r.get('test_sha256',r.get('checker_sha256'))==sha(ROOT/'standalone'/checker),name
  for row in r['cases']:
   if 'passed' in row:assert row['passed'],(name,row)
   elif name=='zmodem-name-ui-checks.json':assert row['visible'] and row['restored'],row
   elif name=='carrier-transfer-deadline-checks.json':
    assert row['fault']==0 and row['installed_exact'] and row['handles_closed'] and row['remaining_peer_steps']==0,row
   elif name=='zmodem-upload-response-checks.json':
    label=row['case']
    expected=2 if label.startswith('escape-') else 4 if label.startswith('carrier-') else 3 if label in ('silent-peer','noise-without-accepted-progress') else None if label in ('direct-policy-unchanged','disconnected-policy-unchanged') else 0
    assert row['status']==expected and bool(row['expected_early_replay'])==(expected is None),row
    if expected is None:assert row['witness'],row
   else:raise AssertionError(('Unrecognized regression result',name,row))
  regressions.append(summarize(path,r))
 paced,protocol=verify_paced(paced_path,host['library_sha256'],6000,8192,35,True)
 conservative,conservative_protocol=verify_paced(conservative_path,host['library_sha256'],1200,256,33,False)
 old_path=ROOT/'build/bbs-lab/sexyz-active-replay-paced-default6000-01/result.json';old=read(old_path)
 assert not old['passed'] and old['status']==4 and old['session_position']==15360 and old['helper_exit']==255
 assert all(row['original_hex']==row['replacement_hex'] for row in old['offers'])
 for name,d in old['inputs'].items():assert sha(old_path.parent/'frozen-source'/name)==d,name
 for name,d in old['captures_sha256'].items():assert sha(old_path.parent/name)==d,name
 assert old['helper_sha256']==paced['helper_sha256']
 custody=ROOT/'build/zmodem-active-replay'/('accepted-'+digest[:12]);assert not custody.exists();custody.mkdir()
 selected=[binary,ROOT/'build/terminal/terminal.map',manifest_path,host_path,linked_path,dos_path,faults_path,exit_path]
 selected += [ROOT/row['result'] for row in regressions]
 kept={}
 for path in selected:
  copy=custody/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,copy)
  assert sha(copy)==sha(path);kept[str(copy.relative_to(ROOT))]=sha(copy)
 result=dict(passed=True,component_only=True,terminal_sha256=digest,
  terminal_manifest_sha256=sha(manifest_path),terminal_source_inputs=manifest['sources'],memory_layout=manifest['memory_layout'],
  host=summarize(host_path,host),actual_DOS=summarize(dos_path,dos),file_owner_faults=summarize(faults_path,faults),linked=summarize(linked_path,linked),
  normal_regressions=regressions,regression_exit=dict(result=str(exit_path.relative_to(ROOT)),sha256=sha(exit_path)),
  stock_paced_host=dict(result=str(paced_path.relative_to(ROOT)),sha256=sha(paced_path),checks=paced['checks'],
   bps_ceiling=6000,source_bytes=65797,source_sha256=paced['source_sha256'],helper_sha256=paced['helper_sha256'],
   receiver_library_byte_identical_to_current_host=True,library_sha256=paced['library_sha256'],default_offers_byte_identical=True,
   verified_old_prefix_operations=len(paced['readback_operations']),protocol=protocol,capture_sha256=paced['captures_sha256']),
  conservative_paced_host=dict(result=str(conservative_path.relative_to(ROOT)),sha256=sha(conservative_path),checks=conservative['checks'],
   bps_ceiling=1200,source_bytes=65797,source_sha256=conservative['source_sha256'],helper_sha256=conservative['helper_sha256'],
   receiver_library_byte_identical_to_current_host=True,library_sha256=conservative['library_sha256'],default_offers_byte_identical=False,
   explicit_wrapper_flags=33,explicit_wrapper_credit=256,native_negotiation_accepted=False,
   verified_old_prefix_operations=len(conservative['readback_operations']),protocol=conservative_protocol,capture_sha256=conservative['captures_sha256']),
  retained_stock_counterexample=dict(result=str(old_path.relative_to(ROOT)),sha256=sha(old_path),status=4,verified_position=15360,
   scope='Actual completed earlier stock helper experiment. Retry debt exhausted on forward verified recovery; not an intentional stop.'),
  custody_sha256=kept,recorder_sha256=sha(Path(__file__)),
  scope='Checked active-stage readback, framed resume recovery and bounded retry accounting. Current source-built DOS component and linked terminal cases are distinct from the stock6000bps paced host-helper capture, whose receiver library is byte-identical to the current host build. No current DOS/BBS/audio,1200bps native negotiation, arbitrary-duration sustained load, physical Boca/SPA2102 or full F01-F16 application acceptance.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,terminal_sha256=digest,host=39,DOS=97,file_faults=64,linked=14,stock_paced_host=True)))

if __name__=='__main__':main()
