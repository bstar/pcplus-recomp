#!/usr/bin/env python3
"""Bind compact interpreter formatting to successful nested DOS compilation."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from prove_compact_runtime_source import ROOT,SPECIAL
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def geometry(p):
 raw=p.read_bytes();w=struct.unpack_from('<14H',raw);assert w[0]==0x5a4d
 size=w[2]*512-(512-w[1]if w[1]else 0);assert size<=len(raw)
 return dict(sha256=sha(p),file_bytes=len(raw),minimum_process_bytes=(((size-w[4]*16+15)//16)+w[5]+16)*16,stack_bytes=w[8])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 base=a.proof.resolve();assert base.is_relative_to(ROOT/'build');proof=load(base/'result.json');assert proof['passed']and not proof['original_inputs']
 sources=dict(proof['sources']);custody={};checks={}
 def bind(path):
  path=path.resolve();assert path.is_relative_to(ROOT);custody[str(path.relative_to(ROOT))]=sha(path)
 def validate_sources(mapping):
  for name,digest in mapping.items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 validate_sources(sources);bind(base/'result.json')
 for label,digest in proof['logs'].items():
  path=base/(label+'.log');assert sha(path)==digest;bind(path)
 for name,digest in proof['reports'].items():
  path=base/'source'/name;data=load(path);assert sha(path)==digest and data['passed'];bind(path)
  if name.endswith('/result.json'):
   assert all(data['checks'].values())and data['products']['TERMINAL.EXE']==proof['products'][SPECIAL]
   assert data['products']['ASPECT.EXE']==proof['products']['aspect-register-parent-custom-irq']
   for artifact,expected in data['artifacts'].items():
    file=base/'source'/artifact;assert sha(file)==expected;bind(file)
   if data['case']=='explicit':assert data['log_collisions']==32
   checks[data['case']]=data['checks']
  elif 'format/'in name:assert data['DOS']==data['host']=='COMPACT_FORMAT 3907 cases 0 failures'
  elif 'aspect-runner/'in name:assert data['DOS_summary']=='RUNNER 21 cases 105 checks 0 failures'
  elif 'aspect-source-compile/'in name:assert data['DOS_summary']=='SOURCE_EXEC 22 cases 223 checks 0 failures'
 assert set(checks)=={'explicit','fallback','chain','rejected'}
 old=ROOT/'build/native-bank-nested/acceptance-experimental-01/ASPECT.EXE'
 current=ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE';before=geometry(old);after=geometry(current)
 assert before['sha256']=='0a09b42a763a7047bd46fd1bd158a046f2d12d9272ae3af63d60221e0161af7c'
 assert after['sha256']==proof['products']['aspect-register-parent-custom-irq']
 assert before['stack_bytes']==after['stack_bytes']==8192
 assert before['minimum_process_bytes']-after['minimum_process_bytes']==2656
 bind(old);bind(current)
 listing=current.parent/'ASPECT.map';text=listing.read_text();assert not re.search(r'\b(?:sprintf_|vsprintf_|fprintf_|__prtf_)\b',text);bind(listing)
 old_report=ROOT/'build/native-bank-nested/acceptance-experimental-01/result.json';failed=load(old_report)
 assert not failed['passed']and failed['products']['TERMINAL.EXE']==proof['products'][SPECIAL]
 assert failed['products']['ASPCOMP.EXE']==proof['products']['aspect-compiler-dos'];bind(old_report)
 regression_paths=['build/aspect-runtime/checks.json','build/aspect-enumeration-dos/compact-format-01/checks.json',
  'build/aspect-file-times-dos/compact-format-01/checks.json','build/aspect-system-query-dos/compact-format-01/checks.json']
 regressions={}
 for name in regression_paths:
  path=ROOT/name;data=load(path);assert data['passed'];bind(path)
  if 'sources'in data:validate_sources(data['sources'])
  if name==regression_paths[0]:
   manifest=path.parent/'manifest.json';m=load(manifest)
   assert sha(manifest)==data['manifest_sha256'];validate_sources(m['sources']);bind(manifest)
   executable=path.parent/'EXECUTE.EXE';assert sha(executable)==data['binary_sha256'];bind(executable)
   output=path.parent/'RESULT.TXT';assert sha(output)==data['result_sha256'];bind(output)
   checker=ROOT/'standalone/check_aspect_runtime.py';assert sha(checker)==data['check_sha256'];sources[str(checker.relative_to(ROOT))]=sha(checker)
  else:
   assert data['runner_sha256']==proof['products']['aspect-runner']and data['compiler_sha256']==proof['products']['aspect-compiler-dos']
   shared=ROOT/'standalone/test_aspect_script_files_dos.py';assert sha(shared)==data['reused_harness_sha256'];sources[str(shared.relative_to(ROOT))]=sha(shared)
   for artifact,key in [(path.parent/'harness.c','harness_sha256'),(path.parent/'drive/RESULT.TXT','result_sha256')]:
    assert sha(artifact)==data[key];bind(artifact)
   if 'native_control_sha256'in data:
    for artifact,key in [(path.parent/'drive/NATIVE.EXE','native_control_sha256'),(path.parent/'drive/NATIVE.TXT','native_control_result_sha256')]:
     assert sha(artifact)==data[key];bind(artifact)
  if 'checker_sha256'in data:
   checker={'build/aspect-runtime/checks.json':'standalone/check_aspect_runtime.py',
    regression_paths[1]:'standalone/test_aspect_enumeration_dos.py',regression_paths[2]:'standalone/test_aspect_file_times_dos.py',
    regression_paths[3]:'standalone/test_aspect_system_query_dos.py'}[name]
   assert sha(ROOT/checker)==data['checker_sha256'];sources[checker]=sha(ROOT/checker)
  regressions[name]=data['DOS_summary']
 for name in ['src/aspect/enumeration_runtime.c','src/aspect/runtime_format.h','src/aspect/runner_error.h']:
  sources[name]=sha(ROOT/name)
 uart_path=ROOT/'build/compact-source-serial-01/checks.json';uart=load(uart_path);bind(uart_path)
 assert uart['passed']and uart['runner_sha256']==proof['products']['aspect-runner']and uart['compiler_sha256']==proof['products']['aspect-compiler-dos']
 for name,key in [('standalone/check_aspect_source_serial_dos.py','checker_sha256'),('standalone/test_aspect_script_serial_dos.py','reused_checker_sha256')]:
  assert sha(ROOT/name)==uart[key];sources[name]=uart[key]
 assert {case['name']for case in uart['cases']}=={'sourceflowN','sourceflowS','sourceflowH','sourceflowB','pressureS','pressureH','pressureB'}
 for case in uart['cases']:
  assert case['passed']and all(case['checks'].values());folder=uart_path.parent/case['name']
  for leaf,key in [('transmitted.bin','tx_hex'),('received-stimulus.bin','input_hex'),('RETURN.BIN','returned_hex'),('STDOUT.BIN','stdout_hex'),('STDERR.BIN','stderr_hex')]:
   assert (folder/leaf).read_bytes().hex()==case[key]
  assert (folder/'STATUS.TXT').read_text().strip()==case['status']
  assert sha(folder/'ASPECT.EXE')==proof['products']['aspect-runner']
  if case['name'].startswith('pressure'):
   first,last=struct.unpack('<II',(folder/'COMPTIME.BIN').read_bytes());assert last-first>=36
   assert sha(folder/'REALCOMP.EXE')==proof['products']['aspect-compiler-dos']
  else:assert sha(folder/'ASPCOMP.EXE')==proof['products']['aspect-compiler-dos']
  for artifact in folder.iterdir():
   if artifact.is_file():bind(artifact)
 output=dict(passed=True,nested_compiler_gate='passed for four recorded bare DOS8086 cases',accepted_for_card_deployment=False,
  sources=sources,source_files=len(sources),source_only_products=proof['products'],before=before,after=after,
  saved_minimum_process_bytes=2656,stack_unchanged=True,general_printf_engine_absent=True,nested_checks=checks,
  regressions=regressions,UART_compiler_cases=uart['cases'],artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],
  limitations=['Original compiler and optional terminal bytes unchanged; this intentionally changes ASPECT.',
   'No arbitrary low-memory driver guarantee, normal width transaction or new BBS/physical hardware acceptance.',
   'Historical failed receipt retained; staged package and card unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(output,indent=2)+'\n')
 print('PASS compact runtime: 2656 bytes reclaimed, four nested cases, exact CRT formats and native consumers; card deployment remains separate')
if __name__=='__main__':main()
