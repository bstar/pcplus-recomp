#!/usr/bin/env python3
"""Freeze parameter/string recovery and composed DOS ownership evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(path.read_bytes())
def read(path):return json.loads((ROOT/path).read_text())
def main():
 sources={};local={}
 def retain(path):local[path]=sha(ROOT/path);return read(path)
 def bind(path,value):
  assert sha(ROOT/path)==value,path
  assert path not in sources or sources[path]==value,path
  sources[path]=value
 modules={}
 for name in ['parameters','strings','runtime']:
  base=f'build/aspect-{name}/';manifest=retain(base+'manifest.json');normal=retain(base+'checks.json');native=retain(base+'checks-native.json')
  assert normal['passed'] and native['passed'] and normal['original_inputs']==[]
  assert manifest['original_inputs']==[]
  if name in ['strings','runtime']:
   assert normal['manifest_sha256']==native['manifest_sha256']==local[base+'manifest.json']
  if name=='parameters':assert normal['flat_sha256']==native['flat_sha256']==manifest['flat_sha256']
  for path,value in manifest['sources'].items():bind(path,value)
  checker_key='harness_sha256' if name=='strings' else 'check_sha256'
  bind(f'standalone/check_aspect_{name}.py',normal[checker_key]);assert normal[checker_key]==native[checker_key]
  binary=normal['DOS']['binary_sha256'] if name=='strings' else normal['binary_sha256']
  native_binary=native['DOS']['binary_sha256'] if name=='strings' else native['binary_sha256']
  assert binary==native_binary==manifest['binary_sha256']
  optional=native['optional_original'];assert optional.get('original_sha256',optional.get('sha256'))==ORIGINAL
  modules[name]=dict(manifest=manifest,source_only_checks=normal,optional_native=optional)
 params,strings,runtime=[modules[k] for k in ['parameters','strings','runtime']]
 assert params['optional_native']['exact_parameter_bytes']==66
 assert params['source_only_checks']['cpu_scenarios']==params['optional_native']['paired_cpu_scenarios']==3901
 assert params['source_only_checks']['visited_instructions']==30
 bind('standalone/check_aspect_operands.py',params['source_only_checks']['inherited_checker_sha256'])
 assert strings['optional_native']['exact_string_bytes']==617
 assert strings['source_only_checks']['cases']==strings['optional_native']['identical_cpu_records']==2251
 bind('standalone/check_aspect_operands.py',strings['source_only_checks']['inherited_checker_sha256'])
 bind('standalone/check_aspect_flow.py',strings['source_only_checks']['inherited_flow_checker_sha256'])
 failed=retain('build/aspect-strings/failed-check-01.json')
 assert failed['CPU_records_sha256']==strings['source_only_checks']['records_sha256']
 record_path='build/aspect-strings/cpu-records.json';local[record_path]=sha(ROOT/record_path)
 assert strings['source_only_checks']['records_sha256']==read('build/aspect-strings/checks-native.json')['records_sha256']==local[record_path]
 corpus=retain('standalone/fixtures/aspect_parameter_vectors.json')
 bind('standalone/aspect_parameter_probe.py',corpus['probe_sha256'])
 bind('standalone/freeze_aspect_parameters.py',corpus['freezer_sha256'])
 report=retain(corpus['private_report']);assert local[corpus['private_report']]==corpus['private_report_sha256']
 assert len(report['cases'])==40 and sum(c['success'] for c in report['cases'])==27
 assert len(corpus['vectors'])==27 and len(corpus['rejected'])==13
 prior=retain(corpus['prior_canonical_report']);assert local[corpus['prior_canonical_report']]=='5cc33c2af6f3ced0a4fee56a00bdfba19442e706a8e34fd8308aec00967d1ec2'
 current={c['name']:c for c in report['cases']};assert sum(c['success'] for c in prior['cases'])==24
 for case in prior['cases']:
  if case['success']:assert case['source_sha256']==current[case['name']]['source_sha256'] and case['asx_sha256']==current[case['name']]['asx_sha256']
 for case in corpus['vectors']:
  assert digest(case['source'].encode('ascii'))==case['source_sha256']
  assert digest(bytes.fromhex(case['hex']))==case['asx_sha256']
  assert not case['dos_excluded']
 path='build/aspect-runtime/RESULT.TXT';local[path]=sha(ROOT/path);text=(ROOT/path).read_text()
 normal=runtime['source_only_checks'];native=read('build/aspect-runtime/checks-native.json')
 assert normal['result_sha256']==native['result_sha256']==local[path]
 assert normal['DOS_summary']=='ASPECT_RUNTIME 320 cases 4760 checks 0 failures'
 assert normal['fixture_count']==132
 rows=[]
 for name,*values in re.findall(r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)',text):
  rows.append(dict(zip(['file','error','steps','peak','cleanup','close','integer0','long0'],[name,*map(int,values)])))
 assert len(rows)==runtime['manifest']['diagnostic_case_count']==320
 unsupported=[r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX',r['file'])]
 slots={int(k,16) for k in runtime['manifest']['supported_slots']};assert len(slots)==39
 assert len(unsupported)==normal['unsupported_slot_cases']==176
 assert {int(r['file'][1:4],16) for r in unsupported}==set(range(215))-slots
 for row in unsupported:assert row['error']==3 and row['steps']==1 and row['cleanup']==row['close']==1
 values={(file,key):int(value) for file,key,value in re.findall(r'VALUE (\S+) (integer\d+|long\d+)=(\d+)',text)}
 string_values={(file,key):bytes.fromhex(value) for file,key,value in re.findall(r'STRING (\S+) (string\d+)=([0-9A-F]*)',text)}
 errors={'divide_zero':11,'native_int0':12,'float':4,'budget':6,'stack':9,'unsupported':3}
 for name,fixture in runtime['manifest']['fixture_expectations'].items():
  row=next(r for r in rows if r['file']==name+'.ASX');expected=fixture['expected']
  assert row['error']==errors.get(expected.get('error'),0),(name,row)
  for key,value in expected.items():
   if re.fullmatch(r'(integer|long)\d+',key):assert values[(name+'.ASX',key)]==value,(name,key)
   if re.fullmatch(r'string\d+',key):assert string_values[(name+'.ASX',key)]==value.encode('ascii'),(name,key)
 for name,error,peak in [('STRRECUR.ASX',9,1),('PARZERO.ASX',11,1),('PARFHEAP.ASX',4,1),('STRSHORT.ASX',5,2)]:
  row=next(r for r in rows if r['file']==name)
  assert row['error']==error and row['peak']==peak and row['cleanup']==row['close']==1
 assert runtime['optional_native']['empty_string_builtin']['index']==19
 map_path='build/aspect-runtime/EXECUTE.map';local[map_path]=sha(ROOT/map_path)
 aliases={name:address for address,name in re.findall(r'(?m)^([0-9a-f]{4}:[0-9a-f]{4})\s+(aspect_(?:dispatch_next_script|string_scratch_pointer))\s*$',(ROOT/map_path).read_text())}
 assert len(aliases)==2 and len(set(aliases.values()))==1
 evidence=[]
 for i in range(1,4):
  bundle=retain(f'analysis/aspect-expression/rea-string-0{i}.json')
  evidence += [dict(id=r['evidence_id'],operation=r['operation'],parameters=r['parameters'],subject_sha256=r['subject']['digest']['sha256']) for r in bundle['records']]
 assert len(evidence)==18
 sources['standalone/record_aspect_parameters.py']=sha(Path(__file__).resolve())
 result=dict(passed=True,sources=sources,local_evidence=local,modules=modules,
  compiler=dict(cases=40,accepted=27,rejected=13,expected_completions=23,expected_stops=dict(float=2,stack=1,divide_zero=1),prior_accepted_reproduced=24,findings=corpus['findings']),
  native_E104_aliases=aliases,retained_fixture_failure=failed,
  runtime_cases=[r for r in rows if r not in unsupported],string_values={f'{name}:{key}':value.decode('ascii') for (name,key),value in string_values.items()},unsupported_count=176,static_evidence=evidence,
  maintained_policy='Actual far-string storage and native81-byte scratch reads/writeback; owner clears pending scratch references after unwind. Diagnostics snapshot string values before real free. String builtin19 returns an owned81-byte empty buffer; all others abort.',
  limitations=['Only39of215 opcode slots wired;176 abort explicitly.',
   'Component opaque parameter readers and CRT/builtin/error models remain separate from actual composed file/heap/string execution.',
   'Native short fread and unchecked index/type/frame/scratch arithmetic remain in recovered code; checked composition aborts short reads but is not arbitrary-bytecode safe.',
   'No float mathematics, complete string commands/builtins, source compiler, recorder or terminal integration; all whole-application gates remain open.'])
 out=ROOT/'docs/validation/aspect-parameters.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out.relative_to(ROOT))
if __name__=='__main__':main()
