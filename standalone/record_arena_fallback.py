#!/usr/bin/env python3
"""Seal compiler heap admission without treating it as complete width acceptance."""
import argparse,hashlib,json,struct
from pathlib import Path
from prove_arena_fallback_source import ROOT,FULL
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def geometry(p):
 raw=p.read_bytes();w=struct.unpack_from('<14H',raw);assert w[0]==0x5a4d
 size=w[2]*512-(512-w[1]if w[1]else 0);assert size<=len(raw)
 return dict(sha256=sha(p),file_bytes=len(raw),minimum_process_bytes=(((size-w[4]*16+15)//16)+w[5]+16)*16,stack_bytes=w[8])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=a.proof.resolve();assert base.is_relative_to(ROOT/'build');proof=load(base/'result.json');assert proof['passed']and not proof['original_inputs']
 sources=dict(proof['sources']);custody={};nested={};summaries={}
 def bind(path):
  path=path.resolve();assert path.is_relative_to(ROOT);custody[str(path.relative_to(ROOT))]=sha(path)
 def add(mapping):
  for name,digest in mapping.items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 add(sources);bind(base/'result.json')
 for name,digest in proof['logs'].items():
  path=base/(name+'.log');assert sha(path)==digest;bind(path)
 for name,digest in proof['reports'].items():
  path=base/'source'/name;data=load(path);assert data['passed']and sha(path)==digest;bind(path)
  if name.startswith('build/nested/'):
   assert all(data['checks'].values())and data['products']['TERMINAL.EXE']==proof['products'][FULL]
   assert data['products']['ASPCOMP.EXE']==proof['products']['aspect-compiler-dos']
   assert data['products']['ASPECT.EXE']==proof['products']['aspect-register-parent-custom-irq']
   for artifact,expected in data['artifacts'].items():
    file=base/'source'/artifact;assert sha(file)==expected;bind(file)
   nested[data['case']]=data['checks']
  elif 'allocator/'in name:
   add(data['sources']);assert 'failures0'in data['summaries']['CONTROL']and'failures0'in data['summaries']['FALLBACK']
   for artifact,expected in data['artifacts'].items():
    file=path.parent/artifact;assert sha(file)==expected;bind(file)
   summaries['allocator']=data['summaries']
  elif name.endswith('/stack-checks.json'):
   assert data['candidate_CLI_stack_bytes']==data['checked_CLI_stack_bytes']==24576
   assert data['checked_API_stack_bytes']==16384 and data['checked_CLI_cases']==18
   summaries['stack']=dict(API_bytes=16384,CLI_bytes=24576,CLI_cases=18)
  elif name=='build/corpus-stack/checks.json':
   assert data['case_count']==2043 and data['accepted']==1077 and data['rejected']==966
   assert data['binary_sha256']==proof['products']['aspect-compiler-dos']
   cases=load(path.parent/'cases.json');assert sha(path.parent/'cases.json')==data['case_manifest_sha256']
   for i,case in enumerate(cases):
    for leaf,key in [(f'P{i:05}.ASP','source_sha256'),(f'P{i:05}.ASX','asx_sha256')]:
     # The sealed case manifest already owns these indexed hashes. Check
     # every file, then bind that manifest once rather than duplicating it.
     file=path.parent/'tests'/leaf;assert sha(file)==case[key]
   bind(path.parent/'cases.json');summaries['corpus']=dict(cases=2043,accepted=1077,rejected=966)
  elif 'workspace/'in name:
   assert data['summary']=='WORKSPACE 11306 bytes VALUE 18 NODE 24 CHECKS 12746 FAILURES 0';summaries['workspace']=data['summary']
 assert set(nested)=={'explicit','fallback','chain','rejected'}
 unit=ROOT/'build/aspect-compiler-unit/checks.json';report=load(unit);manifest=load(unit.parent/'manifest.json')
 assert report['passed']and report['case_count']==2015;add(manifest['sources'])
 assert sha(unit.parent/'ASPINV.EXE')==report['binary_sha256']==manifest['binary_sha256']
 assert report['checker_sha256']==sha(ROOT/'standalone/check_aspect_compiler_unit.py')
 bind(unit);bind(unit.parent/'manifest.json');bind(unit.parent/'ASPINV.EXE');sources['standalone/check_aspect_compiler_unit.py']=report['checker_sha256']
 summaries['unit']=report['DOS_summary']
 uart_path=ROOT/'build/arena-source-serial-01/checks.json';uart=load(uart_path)
 assert uart['passed']and uart['compiler_sha256']==proof['products']['aspect-compiler-dos']and len(uart['cases'])==7;bind(uart_path)
 for name,key in [('standalone/check_aspect_source_serial_dos.py','checker_sha256'),('standalone/test_aspect_script_serial_dos.py','reused_checker_sha256')]:
  assert sha(ROOT/name)==uart[key];sources[name]=uart[key]
 for case in uart['cases']:
  assert case['passed']and all(case['checks'].values());folder=uart_path.parent/case['name']
  for leaf,key in [('transmitted.bin','tx_hex'),('received-stimulus.bin','input_hex'),('RETURN.BIN','returned_hex'),('STDOUT.BIN','stdout_hex'),('STDERR.BIN','stderr_hex')]:assert(folder/leaf).read_bytes().hex()==case[key]
  if case['name'].startswith('pressure'):
   first,last=struct.unpack('<II',(folder/'COMPTIME.BIN').read_bytes());assert last-first>=36
   assert sha(folder/'REALCOMP.EXE')==proof['products']['aspect-compiler-dos']
  else:assert sha(folder/'ASPCOMP.EXE')==proof['products']['aspect-compiler-dos']
  for file in folder.iterdir():
   if file.is_file():bind(file)
 old=ROOT/'build/reset-live-nested-02/explicit/ASPCOMP.EXE';new=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
 before=geometry(old);after=geometry(new);assert before['stack_bytes']==after['stack_bytes']==24576
 assert after['sha256']==proof['products']['aspect-compiler-dos'];bind(old);bind(new)
 prior=ROOT/'docs/validation/reset-live.json';assert not load(prior)['nested_compiler']['passed'];bind(prior)
 result=dict(passed=True,nested_compiler_gate='passed for the transaction parent in four recorded DOS8086 workflows',accepted_for_card_deployment=False,
  sources=sources,source_files=len(sources),source_only_products=proof['products'],summaries=summaries,nested_checks=nested,
  UART_cases=uart['cases'],before=before,after=after,stream_buffer_bytes_borrowed_from_reserved_stack=1024,
  physical_arena_attempts_bounded=10,artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Compiler changed; parent and ASPECT binaries unchanged. No smaller stack, grammar or source bounds.',
   'Nested trials link the transaction API but do not run scripts with an active132-column viewport.',
   'No arbitrary low-memory guarantee; peer width/protected-field/general-row/UI/BBS/physical acceptance remains open.',
   'The failed transaction receipt is historical; package and card remain unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS compiler admission: pooled fallback, borrowed buffers, grammar/stack/ownership, four nested workflows and seven UART cases')
if __name__=='__main__':main()
