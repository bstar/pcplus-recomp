#!/usr/bin/env python3
"""Bind sparse numeric capacity, full VM, ALARM and modern BBS regressions."""
import hashlib,json,re,struct,subprocess
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
 parent=ROOT/'build/terminal-alarm-policy-admission-20261106';child=ROOT/'build/aspect-alarm-numeric-groups-final-20261106'
 products={'TERMINAL.EXE':sha(parent/'TERMINAL.EXE'),'ASPECT.EXE':sha(child/'ASPECT.EXE')}
 for folder,binary in ((parent,'TERMINAL.EXE'),(child,'ASPECT.EXE')):
  path=folder/'manifest.json';r=json.loads(path.read_text());assert r['binary_sha256']==products[binary];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  if binary=='ASPECT.EXE':assert r['startup_heap_growth_bytes']==512 and r['experimental_alarm_VM']
 unit=load('build/numeric-groups-unit-final-20261106/result.json','sources');assert unit['checks']==33341 and unit['allocations']==305 and unit['frees']==300
 vm=[]
 for leaf,strings in [('numeric-groups-vm-final-20261106',False),('numeric-groups-strings-final-20261106',True),('numeric-groups-static-control-20261106',False)]:
  folder=ROOT/'build'/leaf;r=load('build/'+leaf+'/result.json','sources');assert len(r['cases'])==512 and len(r['deep_cases'])==2 and r['with_far_global_strings']==strings
  assert {(v['kind'],v['slot'])for v in r['cases']}=={(k,i)for k in (0,1)for i in range(256)}
  for row in r['cases']+r['deep_cases']:
   assert sha(folder/(row['name']+'.ASX'))==row['ASX_sha256'] and sha(folder/(row['name']+'.TXT'))==row['output_sha256']
  if 'control'not in leaf:assert r['runner_sha256']==products['ASPECT.EXE']
  vm.append(r)
 assert vm[0]['cases']==vm[2]['cases']and vm[0]['deep_cases']==vm[2]['deep_cases']
 aliases=[]
 for leaf in ('numeric-groups-alias-checked-20261106','numeric-groups-alias-control-20261106'):
  r=load('build/'+leaf+'/result.json','sources');assert len(r['cases'])==10
  for row in r['cases']:
   assert sha(ROOT/'build'/leaf/(row['name']+'.ASX'))==row['ASX_sha256']and sha(ROOT/'build'/leaf/(row['name']+'.TXT'))==row['output_sha256']
  aliases.append(r)
 assert aliases[0]['runner_sha256']==products['ASPECT.EXE']and aliases[0]['cases']==aliases[1]['cases']
 full=load('build/numeric-groups-full-runtime-20261106/numeric-checks.json','sources');assert full['supported_slots']==107 and full['DOS_summary']=='ASPECT_RUNTIME 1123 cases 26986 checks 0 failures'
 assert sha(ROOT/'build/numeric-groups-full-runtime-20261106/checks.json')==full['base_checks_sha256']
 base='build/aspect-alarm-vm-dos/numeric-groups-matrix-20261106/'
 matrix=load(base+'pause-checks.json');detail=load(base+'checks.json')
 assert matrix['parent_sha256']==products['TERMINAL.EXE']and matrix['runner_sha256']==products['ASPECT.EXE']and len(matrix['cases'])==len(detail['cases'])==5
 for name,h in matrix['captures_sha256'].items():assert sha(ROOT/base/name)==h,name
 for row in matrix['cases']:assert row['passed']and all(row['checks'].values())
 capacities=[]
 for leaf,cpu,checks,held in [('alarm-numeric-groups-capacity-first-20261106','386',27,True),('alarm-numeric-groups-capacity-8086-20261106','8086',26,False)]:
  r=load('build/'+leaf+'/result.json','sources');assert r['binary_sha256']==products['TERMINAL.EXE']and r['interpreter_sha256']==products['ASPECT.EXE']
  assert len(r['checks'])==checks and all(r['checks'].values())and r['cpu']==cpu and r['held_streams']==held and r['streams_around_child']and r['clock_queries']and r['nested_child_count']==3
  capacities.append(r)
 before=load('build/alarm-run-result-capacity-20261106/result.json',passed=False)
 after=load('build/alarm-groups-result-capacity-20261106/result.json','sources');bw,aw=before['exit_watch'],after['exit_watch']
 assert before['binary_sha256']==after['binary_sha256']==products['TERMINAL.EXE']
 failed=[v for v in bw['allocations']if v['carry']];assert len(failed)==1 and (failed[0]['paragraphs'],failed[0]['ax'],failed[0]['bx'])==(38,8,7)
 assert bw['program_results'][1]['status']==7 and bw['program_results'][1]['crt_error']==12 and bw['program_results'][1]['dos_error']==8
 assert not any(v['carry']for v in aw['allocations'])and len(aw['exits'])==4
 for i in (0,1,3):assert aw['program_results'][i]['stage']==2 and aw['program_results'][i]['status']==aw['program_results'][i]['process_status']==0
 assert all(v['exit']==v['error']==v['cleanup_error']==0 for v in aw['exits'])
 negative_manifest=ROOT/'build/aspect-alarm-run-result-diagnostic-20261106/manifest.json';nm=json.loads(negative_manifest.read_text());old_source=subprocess.check_output(['git','show','568aeb3:src/aspect/numeric_bank_runtime.c'],cwd=ROOT)
 assert nm['sources']['src/aspect/numeric_bank_runtime.c']==hashlib.sha256(old_source).hexdigest();receipts[str(negative_manifest.relative_to(ROOT))]=sha(negative_manifest)
 cold=load('build/alarm-numeric-groups-cold-20261106/result.json','overlay_sources');assert cold['products']==products and cold['source_files']==5397
 inventory=ROOT/'build/alarm-numeric-groups-cold-20261106/inventory.json';assert sha(inventory)==cold['inventory_sha256']and len(json.loads(inventory.read_text()))==5397
 assert cold['results']['unit']['cases']==33341 and cold['results']['numeric']['cases']==cold['results']['strings']['cases']==512 and cold['results']['numeric']['deep_cases']==cold['results']['strings']['deep_cases']==2 and cold['results']['ALARM']['cases']==1
 sync=load('build/bbs-lab/results/synchronet/alarm-groups-sync-size-20261106/proxy-integration.json');assert sync['binary_sha256']==products['TERMINAL.EXE']and sync['interpreter_sha256']==products['ASPECT.EXE']and all(sync['checks'].values())and sync['external_viewer']['passed']
 for n,h in sync['product_inputs'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 carrier=load('build/bbs-lab/results/enigma/alarm-groups-carrier-long-20261106/carrier-checks.json','sources');assert all(carrier['checks'].values())and carrier['transfer_wait_ms']==150000
 audit=load('build/alarm-groups-carrier-audit-20261106/result.json','sources');assert audit['exact_retry_bytes']==65539
 assert audit['products']['TERMINAL.EXE']['sha256']==products['TERMINAL.EXE']and audit['products']['ASPECT.EXE']['sha256']==products['ASPECT.EXE']
 for n,h in audit['captures'].items():assert sha(ROOT/n)==h,n
 default=sha(ROOT/'build/aspect-runner/ASPECT.EXE');assert default=='91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
 for n in ('standalone/record_alarm_groups.py','standalone/test_aspect_alarm_vm_dos.py','standalone/aspect_exit_watch.py','standalone/aspect_exit_watch.asm'):sources[n]=sha(ROOT/n)
 report=dict(passed=True,release_accepted=False,sources=sources,receipts=receipts,products=products,default_interpreter_sha256=default,
  summary=dict(bank_API_checks=33341,allocation_failures=5,native_slot_VM_cases=1024,deep_expression_VM_cases=4,mixed_view_alias_cases=10,full_VM_cases=1123,full_VM_checks=26986,base_slots=107,ALARM_parent_cases=5,capacity_386_checks=27,capacity_8086_checks=26,cold_source_files=5397,cold_ALARM_cases=1,Enigma_exact_retry_bytes=65539),
  minimum_process_bytes_including_PSP=dict(parent=minimum(parent/'TERMINAL.EXE'),child=minimum(child/'ASPECT.EXE')),
  before_after_diagnostic=dict(before_DOS_request_bytes=38*16,before_largest_free_bytes=7*16,before_DOS_error=8,before_native_errno=12,after_all_calls_succeed=True,diagnostic_overhead_not_a_production_free_block_measurement=True),
  limitations=['Sparse storage preserves all256system/128float elements, per-element8-byte extent and stable acquired addresses, not cross-group contiguity. Current typed consumers use2/4/8-byte values. Future raw bank walkers require separate review.',
   'Far globals materialize all groups first; allocation metadata can exceed the former dense representation. This is not a universal peak-memory reduction. Float arithmetic remains unsupported.',
   'ALARM matrix covers explicit quiet4-count alerts, standard BIOS/ANSI and UMB observer. Default/range/key/sound/long-budget/carrier ALARM expansion and physical acceptance remain open.',
   'Cold rebuild repeats bank API,1024slot/fourdeep cases and oneALARM case, not mixed aliases/full1123VM/capacity/BBS suites.',
   'Synchronet/Enigma use owned stock loopback laboratories and staged actual SynthModem Telnet code. No physical SPA2102/SIP/DSP/analog/CTS-stall acceptance. Initial wrong-Nix/display-mode/60s-cutoff attempts are not accepted gates.',
   'No release package selection, physical deployment, private config/history or live BBS/bridge changes. Full original parity remains open.'],scope=__doc__)
 (ROOT/'docs/validation/aspect-alarm-groups.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS sparse numeric capacity/full VM/ALARM/modern BBS checkpoint')
if __name__=='__main__':main()
