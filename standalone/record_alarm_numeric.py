#!/usr/bin/env python3
"""Bind ALARM numeric-bank/real-WHEN evidence without accepting the failed release gate."""
import json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def minimum(path):
 w=struct.unpack_from('<14H',path.read_bytes());module=w[2]*512-(512-w[1]if w[1]else 0)-w[4]*16
 return (((module+15)//16)+w[5]+16)*16

def main():
 sources={};receipts={}
 def load(name,field=None,passed=True):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed']==passed,name;receipts[name]=sha(path)
  if field:
   for n,h in r[field].items():
    assert sha(ROOT/n)==h,n
    if n in sources:assert sources[n]==h,n
    sources[n]=h
  return r
 parent=ROOT/'build/terminal-alarm-policy-admission-20261106';child=ROOT/'build/aspect-alarm-vm-numeric-final-20261106'
 products={'TERMINAL.EXE':sha(parent/'TERMINAL.EXE'),'ASPECT.EXE':sha(child/'ASPECT.EXE')}
 for folder,binary in ((parent,'TERMINAL.EXE'),(child,'ASPECT.EXE')):
  path=folder/'manifest.json';r=json.loads(path.read_text());assert r['binary_sha256']==products[binary];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 unit=load('build/numeric-banks-dos-prepared-20261106/result.json','sources');assert unit['checks']==33115 and unit['allocations']==214 and unit['frees']==210
 rows=[]
 for leaf,strings in [('numeric-bank-vm-final-20261106',False),('numeric-bank-vm-strings-final-20261106',True),('numeric-bank-vm-control-final-20261106',False)]:
  folder=ROOT/'build'/leaf;r=load('build/'+leaf+'/result.json','sources');assert len(r['cases'])==512 and r['with_far_global_strings']==strings
  assert {(v['kind'],v['slot'])for v in r['cases']}=={(k,i)for k in (0,1)for i in range(256)}
  if 'control'not in leaf:assert r['runner_sha256']==products['ASPECT.EXE']
  for v in r['cases']:
   assert sha(folder/(v['name']+'.ASX'))==v['ASX_sha256'] and sha(folder/(v['name']+'.TXT'))==v['output_sha256']
  rows.append(r)
 assert rows[0]['cases']==rows[2]['cases']
 base='build/aspect-alarm-vm-dos/native-when-matrix-20261106/'
 matrix=load(base+'pause-checks.json');detail=load(base+'checks.json')
 assert matrix['parent_sha256']==products['TERMINAL.EXE']and matrix['runner_sha256']==products['ASPECT.EXE']
 assert len(matrix['cases'])==len(detail['cases'])==5
 assert {c['case']for c in matrix['cases']}=={'alarm-vm-'+n for n in ('transmit','call','framed-call','plain-terminal','two-calls')}
 for name,h in matrix['captures_sha256'].items():assert sha(ROOT/base/name)==h,name
 for row in matrix['cases']:assert row['passed']and all(row['checks'].values())and 0<=row['query_reply_delay_seconds']<1 and 3<=row['pause_complete_after_hold_seconds']<=5
 cold=load('build/alarm-numeric-cold-final-20261106/result.json','overlay_sources')
 assert cold['products']==products and cold['source_files']==5393
 assert sha(ROOT/'build/alarm-numeric-cold-final-20261106/inventory.json')==cold['inventory_sha256']
 assert cold['results']['unit']['cases']==33115 and cold['results']['numeric']['cases']==cold['results']['strings']['cases']==512 and cold['results']['ALARM']['cases']==1
 native=load('build/aspect-operands/checks.json');assert native['cpu_scenarios']==4599
 capacity=load('build/alarm-numeric-parent-capacity-20261106/result.json','sources',passed=False)
 assert capacity['binary_sha256']==products['TERMINAL.EXE']and capacity['interpreter_sha256']==products['ASPECT.EXE']
 assert capacity['streams_around_child']and capacity['held_streams']and capacity['clock_queries']
 rejected={k for k,v in capacity['checks'].items()if not v}
 assert rejected=={'all_six_streams','six_files','three_nested_children','exact_viewport_cells'}
 drive=ROOT/'build/connection-dos/alarm-numeric-parent-capacity-20261106'
 assert b'error 10, opcode 9B, step 26'in(drive/'SCREEN.BIN').read_bytes()[::2]
 default=sha(ROOT/'build/aspect-runner/ASPECT.EXE');assert default=='91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
 for n in ['standalone/record_alarm_numeric.py','standalone/test_aspect_alarm_vm_dos.py','standalone/test_alarm_no_tsr_dos.py']:sources[n]=sha(ROOT/n)
 report=dict(component_tests_passed=True,release_accepted=False,parent_capacity_passed=False,sources=sources,receipts=receipts,products=products,default_interpreter_sha256=default,
  minimum_process_bytes_including_PSP=dict(parent=minimum(parent/'TERMINAL.EXE'),child=minimum(child/'ASPECT.EXE'),preceding_staging_child=minimum(ROOT/'build/aspect-alarm-vm-first-20261106/ASPECT.EXE')),
  summary=dict(bank_API_checks=33115,native_system_VM_cases=1024,preceding_static_control_cases=512,native_operand_CPU_cases=4599,actual_parent_ALARM_cases=5,cold_source_files=5393,cold_repeated_ALARM_cases=1,parent_capacity_checks=27,parent_capacity_passed_checks=23),
  capacity_failure_checks=sorted(rejected),capacity_capture_artifacts={str(f.relative_to(ROOT)):sha(f)for f in drive.iterdir()if f.is_file()},
  limitations=['ALARM matrix uses explicit duration4, quiet parent policy, standard BIOS input, ANSI, synthetic raw modem peer and UMB-resident passive observer. No key is injected during the alert. Default/operand/key/sound/carrier and modern BBS expansion remains open.',
   'MZ launch minimum decreases2800bytes, but far global allocation prepares both full banks first to avoid near-heap fragmentation. This is not a2800-byte peak saving for all scripts.',
   'Native float arithmetic remains unsupported;128float-slot storage/identity is tested at the bank API, not through floating VM operations. Native flat comparison remains separate; deferred adapters add checked indices/allocation failures.',
   'Full parent capacity remains failed: RUN reports error10 at opcode9B step26 around held streams. Do not infer a sole memory/ownership cause yet. No release/deployment accepted.',
   'Cold rebuild repeats all bank API/1024 VM cases and one parent ALARM case, not full WHEN/capacity/BBS/physical coverage. No physical SIP/audio/CTS/DCD acceptance.'],scope=__doc__)
 (ROOT/'docs/validation/aspect-alarm-numeric.json').write_text(json.dumps(report,indent=2)+'\n');print('Recorded component PASS; release NOT accepted; capacity23/27')
if __name__=='__main__':main()
