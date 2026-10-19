#!/usr/bin/env python3
"""Freeze sanitized arithmetic, compiler and actual DOS runtime evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def main():
 sources={};local={}
 def retain(path):local[path]=sha(ROOT/path);return read(path)
 def bind(path,digest):
  assert sha(ROOT/path)==digest,path
  assert path not in sources or sources[path]==digest,path
  sources[path]=digest
 modules={}
 for name in ['long','arithmetic','runtime']:
  base=f'build/aspect-{name}/';manifest=retain(base+'manifest.json');normal=retain(base+'checks.json');native=retain(base+'checks-native.json')
  assert normal['passed'] and native['passed'] and normal['original_inputs']==[]
  assert manifest['binary_sha256']==normal['binary_sha256']==native['binary_sha256']
  for path,digest in manifest['sources'].items():bind(path,digest)
  key='checker_sha256' if name=='long' else 'check_sha256'
  assert normal[key]==native[key]
  bind(f'standalone/check_aspect_{name}.py',normal[key])
  if name in ['long','runtime']:assert normal['manifest_sha256']==native['manifest_sha256']==sha(ROOT/(base+'manifest.json'))
  assert native['optional_original']['original_sha256']==ORIGINAL
  modules[name]=dict(manifest=manifest,source_only_checks=normal,optional_native=native['optional_original'])
 long,arith,runtime=[modules[k] for k in ['long','arithmetic','runtime']]
 assert long['manifest']['bytes']==long['optional_native']['exact_bytes']==535
 assert long['source_only_checks']['cpu_scenarios']==long['optional_native']['paired_cpu_scenarios']==4626
 assert long['source_only_checks']['instruction_addresses']==248
 assert arith['optional_native']['exact_arithmetic_bytes']==665
 assert arith['source_only_checks']['cpu_scenarios']==arith['optional_native']['paired_cpu_scenarios']==3668
 assert arith['manifest']['flat_sha256']==arith['source_only_checks']['flat_sha256']
 bind('standalone/check_aspect_operations.py',arith['source_only_checks']['inherited_checker_sha256'])
 assert runtime['optional_native']['exact_support_bytes']==501
 corpus=retain('standalone/fixtures/aspect_arithmetic_vectors.json')
 assert len(corpus['vectors'])==86
 bind('standalone/aspect_arithmetic_probe.py',corpus['probe_sha256'])
 bind('standalone/freeze_aspect_arithmetic.py',corpus['freezer_sha256'])
 assert sha(ROOT/corpus['private_report'])==corpus['private_report_sha256']
 report=retain(corpus['private_report']);assert len(report['cases'])==88 and sum(c['success'] for c in report['cases'])==86
 findings=retain('analysis/aspect-arithmetic/compiler-02/findings.json')
 assert findings['canonical_report_sha256']==corpus['private_report_sha256']
 for case in corpus['vectors']:
  assert sha_bytes(case['source'].encode('ascii'))==case['source_sha256']
  assert sha_bytes(bytes.fromhex(case['hex']))==case['asx_sha256']
  assert not case['dos_excluded']
 path='build/aspect-runtime/RESULT.TXT';local[path]=sha(ROOT/path);text=(ROOT/path).read_text()
 normal=runtime['source_only_checks'];native=read('build/aspect-runtime/checks-native.json')
 assert normal['result_sha256']==native['result_sha256']==local[path]
 regex=r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)'
 rows=[]
 for name,*values in re.findall(regex,text):rows.append(dict(zip(['file','error','steps','peak','cleanup','close','integer0','long0'],[name,*map(int,values)])))
 assert len(rows)==runtime['manifest']['diagnostic_case_count']==295
 assert normal['DOS_summary']=='ASPECT_RUNTIME 295 cases 3794 checks 0 failures'
 unsupported=[r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX',r['file'])]
 assert len(unsupported)==normal['unsupported_slot_cases']==179
 slots={int(k,16) for k in runtime['manifest']['supported_slots']};assert len(slots)==36
 assert {int(r['file'][1:4],16) for r in unsupported}==set(range(215))-slots
 for row in unsupported:assert row['error']==3 and row['steps']==1 and row['cleanup']==row['close']==1
 actual_values={(file,key):int(value) for file,key,value in re.findall(r'VALUE (\S+) (integer\d+|long\d+)=(\d+)',text)}
 errors={'divide_zero':11,'native_int0':12,'float':4,'budget':6,'stack':9,'unsupported':3}
 for name,fixture in runtime['manifest']['fixture_expectations'].items():
  found=[r for r in rows if r['file']==name+'.ASX'];assert found
  expected=fixture['expected'];assert found[0]['error']==errors.get(expected.get('error'),0),(name,found[0])
  for key,value in expected.items():
   if re.fullmatch(r'(integer|long)\d+',key):assert actual_values[(name+'.ASX',key)]==value,(name,key)
 for name,error in [('HEAPFLT.ASX',12),('HEAPZERO.ASX',11)]:
  row=next(r for r in rows if r['file']==name)
  assert row['error']==error and row['peak']==2 and row['cleanup']==row['close']==1
 bundle=retain('analysis/aspect-expression/rea-arithmetic-01.json')
 evidence=[dict(id=r['evidence_id'],operation=r['operation'],parameters=r['parameters'],subject_sha256=r['subject']['digest']['sha256']) for r in bundle['records']]
 assert len(evidence)==12
 sources['standalone/record_aspect_arithmetic.py']=sha(Path(__file__).resolve())
 result=dict(passed=True,sources=sources,local_evidence=local,modules=modules,
  compiler=dict(cases=88,accepted=86,expected_completions=75,expected_stops=dict(divide_zero=8,native_int0=2,float=1),findings=findings),
  runtime_cases=[r for r in rows if r not in unsupported],unsupported_count=179,static_evidence=evidence,
  maintained_policy='Temporary DOS INT0 vector rewrites saved CS:IP to an abort trampoline and IRETs before native nonlocal unwind. Parent restores prior vector. Every composed case verifies vector and IF/DF restoration. Native recovered code is unchanged.',
  limitations=['Only36of215 opcode slots wired;179 others abort explicitly.',
   'Arithmetic component uses controlled long helpers; separate535-byte native helper checks and composed DOS execution establish actual resident behavior.',
   'Unicorn models later-x86 word CL shifts; component CPU expectations use0..31, actual8086 DOS checks cover0..255. Long helpers shift one bit per iteration and use count low byte.',
   'No floating-point approximation or source compiler; frozen authored original-compiler output supports ordinary original-free tests.',
   'Native unchecked indexing/type/frame arithmetic remains; authored corpus does not prove arbitrary-input safety.',
   'No terminal integration, full ASPECT/recorder/application service coverage or closed whole-application gate.'])
 out=ROOT/'docs/validation/aspect-arithmetic.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(ROOT))
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
if __name__=='__main__':main()
