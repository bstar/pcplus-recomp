#!/usr/bin/env python3
"""Freeze sanitized expression/runtime evidence, preserving provenance boundaries."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(rel):return json.loads((ROOT/rel).read_text())
def main():
 sources={};local={}
 def bind(path,digest):
  assert sha(ROOT/path)==digest,path
  assert path not in sources or sources[path]==digest
  sources[path]=digest
 paths=['build/aspect-operands/manifest.json','build/aspect-operands/checks.json','build/aspect-operands/checks-native.json',
  'build/aspect-operations/manifest.json','build/aspect-operations/cpu-result.json','build/aspect-operations/cpu-result-native.json',
  'build/aspect-operations/cpu-records.json','build/aspect-runtime/manifest.json','build/aspect-runtime/checks.json',
  'build/aspect-runtime/checks-native.json','build/aspect-runtime/RESULT.TXT','analysis/aspect-expression/rea-support-01.json']
 for p in paths:local[p]=sha(ROOT/p)
 operands,oc,on=map(read,paths[:3]);operations,pc,pn=map(read,paths[3:6]);runtime,rc,rn=map(read,paths[7:10])
 assert all(r['passed'] for r in [oc,on,pc,pn,rc,rn])
 assert oc['original_inputs']==pc['original_inputs']==rc['original_inputs']==[]
 assert oc['cpu_scenarios']==on['optional_original']['paired_cpu_scenarios']==4599
 assert on['optional_original']['exact_operand_bytes']==381
 assert on['optional_original']['original_sha256']==ORIGINAL
 assert pc['cases']==pn['private_original_comparison']['identical_cpu_records']==2809
 assert pc['coverage_count']==pn['coverage_count']==464
 assert pc['private_original_comparison'] is None and pn['private_original_comparison']['original_sha256']==ORIGINAL
 assert pc['records_sha256']==pn['records_sha256']==sha(ROOT/paths[6])
 assert pc['manifest_sha256']==pn['manifest_sha256']==sha(ROOT/paths[3])
 assert operations['bytes']==1182
 assert rn['optional_original']['exact_support_bytes']==501 and rn['optional_original']['original_sha256']==ORIGINAL
 assert runtime['binary_sha256']==rc['binary_sha256']==rn['binary_sha256']
 assert rc['manifest_sha256']==rn['manifest_sha256']==sha(ROOT/paths[7])
 assert rc['result_sha256']==rn['result_sha256']==sha(ROOT/paths[10])
 assert len(runtime['supported_slots'])==24 and rc['unsupported_slot_cases']==191
 for manifest,report,checker,key in [(operands,oc,'operands','check_sha256'),(operations,pc,'operations','harness_sha256'),(runtime,rc,'runtime','check_sha256')]:
  for p,d in manifest['sources'].items():bind(p,d)
  bind(f'standalone/check_aspect_{checker}.py',report[key])
 bind('standalone/check_aspect_flow.py',oc['inherited_checker_sha256'])
 assert oc['check_sha256']==on['check_sha256'] and pc['harness_sha256']==pn['harness_sha256'] and rc['check_sha256']==rn['check_sha256']
 assert operands['binary_sha256']==oc['binary_sha256']==on['binary_sha256']
 assert operations['binary_sha256']==pc['DOS']['binary_sha256']==pn['DOS']['binary_sha256']
 corpus=read('standalone/fixtures/aspect_execution_vectors.json')
 bind('standalone/aspect_execution_probe.py',corpus['probe_sha256']);bind('standalone/freeze_aspect_execution.py',corpus['freezer_sha256'])
 assert sha(ROOT/corpus['private_report'])==corpus['private_report_sha256']
 local[corpus['private_report']]=corpus['private_report_sha256']
 rows=[]
 regex=r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)'
 for values in re.findall(regex,(ROOT/paths[10]).read_text()):
  name,*numbers=values
  rows.append(dict(zip(['file','error','steps','peak','cleanup','close','integer0','long0'],[name,*map(int,numbers)])))
 assert len(rows)==runtime['diagnostic_case_count']==219
 unsupported=[r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX',r['file'])]
 assert len(unsupported)==191
 for row in unsupported:assert row['error']==3 and row['steps']==1 and row['cleanup']==row['close']==1 and row['peak']==0
 actual_slots={int(r['file'][1:4],16) for r in unsupported}
 assert actual_slots==set(range(215))-{int(k,16) for k in runtime['supported_slots']}
 # New static evidence is from the synthetic overlay carrier, not original execution.
 bundle=read(paths[11]);evidence=[]
 for record in bundle['records']:
  evidence.append(dict(id=record['evidence_id'],operation=record['operation'],parameters=record['parameters'],subject_sha256=record['subject']['digest']['sha256']))
 sources['standalone/record_aspect_runtime.py']=sha(Path(__file__).resolve())
 result=dict(passed=True,sources=sources,local_evidence=local,
  operands=dict(manifest=operands,source_only_checks=oc,optional_native=on['optional_original']),
  operations=dict(manifest=operations,cpu_cases=pc['cases'],groups=pc['groups'],instruction_coverage=pc['coverage_count'],records_sha256=pc['records_sha256'],DOS=pc['DOS'],optional_native=pn['private_original_comparison']),
  runtime=dict(manifest=runtime,checks=rc,optional_native=rn['optional_original'],cases=[r for r in rows if r not in unsupported],unsupported_count=191),
  compiler_fixture_scope=corpus['scope'],static_memcompare_evidence=evidence,
  limitations=['Only24of215 native opcode slots are wired; all191 others abort, never silently skip.',
   'No source-owned ASPECT compiler yet; normal tests use authored original-compiler output frozen as fixtures.',
   'Native unchecked index/frame/type paths remain; authored fixtures are not proof of arbitrary-bytecode safety.',
   'Float/system/UI/serial/string/arithmetic/parameter services remain incomplete; float models in component tests never provide mathematics.',
   'Runtime is a standalone diagnostic composition, not integrated into TERMINAL; all whole-application gates remain open.'])
 out=ROOT/'docs/validation/aspect-runtime.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(ROOT))
if __name__=='__main__':main()
