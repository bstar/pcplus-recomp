#!/usr/bin/env python3
"""Audit lookup policy, actual DOS targets, heap control and composed witnesses."""
import argparse,json,re,struct,sys
from pathlib import Path
import record_guarded_helper as guarded
from build_guarded_helper import ROOT,LOOKUP
from hook_lookup_fixtures import CASES,fixture
from prove_guarded_helper_source import sha
from test_hook_apply_dos import FIELDS
def load(p):return json.loads(p.read_text())
def reset(raw):
 out=bytearray(raw);out[:20]=bytes(20)
 for i in range(10):out[20+i*81]=0
 return bytes(out)
def seal(raw,epoch):
 value=epoch
 for byte in raw:value=(((value<<1)|(value>>15))&65535)^byte
 return value
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
 p.add_argument('--trap-label',required=True);p.add_argument('--cancel-label',required=True)
 p.add_argument('--sync-label',required=True);p.add_argument('--enigma-label',required=True)
 p.add_argument('--register-prefix',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.root.resolve();assert root.is_relative_to(ROOT/'build')and re.fullmatch('[A-Za-z0-9_-]+',a.register_prefix)
 argv=sys.argv[:]
 try:
  sys.argv=['record_guarded_helper.py','--lookup','--root',str(root),'--trap-label',a.trap_label,
   '--cancel-label',a.cancel_label,'--sync-label',a.sync_label,'--enigma-label',a.enigma_label,'--output',str(root/'guarded-checks.json')]
  guarded.main()
 finally:sys.argv=argv
 result=load(root/'guarded-checks.json');sources=result['sources'];artifacts=result['artifacts']
 def merge(mapping):
  for name,digest in mapping.items():assert sha(ROOT/name)==digest and(name not in sources or sources[name]==digest),name;sources[name]=digest
 def capture(path):
  assert path.is_relative_to(ROOT/'build');artifacts[str(path.relative_to(ROOT))]=sha(path)
 def bind(folder):
  for path in folder.rglob('*'):
   if path.is_file():capture(path)
 capture(root/'guarded-checks.json');terminal=ROOT/'build'/LOOKUP/'TERMINAL.EXE';runner=ROOT/'build/aspect-register-parent/ASPECT.EXE'
 linked=load(root/'final-linked/result.json');plain=load(root/'final-linked-source/result.json')
 assert linked['passed']and plain['passed']and linked['original_comparison']and not plain['original_comparison']
 assert linked['binary_sha256']==plain['binary_sha256']==sha(terminal)
 assert len(linked['cases'])==len(plain['cases'])==28 and len(linked['bounds'])==len(plain['bounds'])==14
 assert sum('native_deviation'in r for r in linked['cases'])==2
 assert linked['original_inputs']['analysis/pcplus-originals/PCPLUS-main-2.01.EXE']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 for name,digest in linked['original_inputs'].items():assert sha(ROOT/name)==digest
 assert not plain['original_inputs'];merge(linked['sources']);merge(plain['sources']);bind(root/'final-linked');bind(root/'final-linked-source')
 # Replay current linked/native policy against the captured event records;
 # a passing producer flag or fabricated native return is not sufficient.
 from check_hook_lookup import Linked,original,vectors,bounds
 def packed(value):return json.loads(json.dumps(value,default=lambda v:{'hex':v.hex()}if isinstance(v,bytes)else None))
 for recorded,vector in zip(linked['cases'],vectors()):
  label,name,env,files,errors,expected=vector;machine=Linked(name,env,files,errors);observed=machine.run()
  native_status,native_events,resolved=original(name,env,files,errors)
  assert recorded['case']==label and recorded['result']==list(observed)and recorded['events']==packed(machine.events)
  assert recorded['original_status']==native_status and recorded['original_resolved']==packed(resolved)
  if 'original_events'in recorded:assert recorded['original_events']==packed(native_events)
 assert linked['bounds']==plain['bounds']==packed(bounds())
 lookups=[]
 for port in(1,2):
  for case in CASES:
   folder=root/f'final-lookup-{port}-{case}';r=load(folder/'result.json');merge(r['sources'])
   helper=(folder/'BUILD/APPLYCH.EXE').read_bytes();name,files,env=fixture(case,helper)
   assert r['passed']and r['mode']==0 and r['port']==port and r['online']and r['committed']and r['status']==0
   assert r['binary_sha256']==sha(terminal)and r['helper_sha256']==sha(folder/'BUILD/APPLYCH.EXE')
   assert r['lookup_case']==case and r['launch_name']==name.decode('ascii')and r['lookup_environment']==env
   assert(folder/'MODE.BIN').read_bytes()==b'\0\0'
   key=(folder/'ACTIONS.KEY').read_bytes();assert struct.unpack_from('<H',key)[0]==2 and key[2:54].split(b'\0',1)[0]==name
   for leaf,data in files.items():assert(folder/leaf).read_bytes()==data,leaf
   assert(folder/'COUNT.BIN').read_bytes()==struct.pack('<H',3)
   before=[(folder/f'B{i}.BIN').read_bytes()for i in range(3)];after=[(folder/f'A{i}.BIN').read_bytes()for i in range(3)]
   assert all(len(raw)==2094 for raw in before+after)and before[1]==after[0]and before[2]==after[1]==before[1]
   for i in range(3):
    raw=(folder/f'S{i}.BIN').read_bytes();assert sha(folder/f'S{i}.BIN')==r['snapshots'][i]and len(raw)==sum(size for _,size in FIELDS)
    if i:assert struct.unpack_from('<H',raw)[0]==0 and struct.unpack_from('<H',raw,4)[0]==i and raw[904:1734]==before[i][:830]
   peer=r['peer'];assert peer['passed']and all(peer['checks'].values())and peer['cpu']=='8086'and peer['environment']==env
   wire=(folder/'serial.bin').read_bytes();assert wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
   assert(folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
   if case=='batch-collision':
    text=(folder/'BATARGS.TXT').read_text().strip();match=re.fullmatch(r'\[\.\\CALL\.BAT\] \[PCPLUS\] \[(\d+)\] \[(\d+)\] \[(\d+)\] \[3\]',text)
    assert match and(folder/'BATSEEN.TXT').read_text().strip()=='START'
    pointers=list(map(int,match.groups()));assert all(p<=4294967295 for p in pointers)
    assert pointers[1]-pointers[0]==20 and pointers[2]-pointers[0]==830 and pointers[0]&65535==16
   lookups.append(dict(port=port,case=case,name=r['launch_name'],environment=env,helper_sha256=r['helper_sha256']))
   bind(folder)
 register=[]
 for port in(1,2):
  for case in('normal','bad-token','missing-script','missing-helper','divide','budget','abort'):
   label=f'{a.register_prefix}-{port}-{case}';folder=ROOT/'build/register-handoff-dos'/label;r=load(folder/'result.json');merge(r['sources'])
   raw=ROOT/'build/connection-dos'/('register-'+label)
   assert r['passed']and r['cpu']=='8086'and r['parent_sha256']==sha(terminal)and r['child_sha256']==sha(runner)
   assert r['DOS']['passed']and all(r['DOS']['checks'].values())
   assert len(r['snapshots'])==(7 if case in('bad-token','divide','budget','abort')else 5)
   for snapshot in r['snapshots']:
    i=snapshot['index'];owner=(raw/f'OWNER{i}.BIN').read_bytes();child=(raw/f'CHILD{i}.BIN').read_bytes()
    assert len(owner)==1734 and len(child)==830 and sha(raw/f'OWNER{i}.BIN')==snapshot['owner_sha256']and sha(raw/f'CHILD{i}.BIN')==snapshot['child_sha256']
    phase,token,epoch,checksum=struct.unpack_from('<4H',owner)
    assert phase==1 and token==snapshot['token']and epoch==snapshot['epoch']and checksum==seal(owner[904:],epoch)
    assert owner[74:904]==reset(owner[904:])
   assert(raw/'BEFORE.BIN').read_bytes()==(raw/'AFTER.BIN').read_bytes()
   wire=(raw/'serial.bin').read_bytes();assert wire.index(b'OBSERVE\r')<wire.index(b'\x1b[0n')
   register.append(dict(port=port,case=case,snapshots=len(r['snapshots']),operand_fixture_patches=r['operand_fixture_patches']))
   bind(raw);capture(folder/'result.json')
 # Same parent, compiler, DOS source and PRM before/after interpreter growth.
 heap=[]
 for attempt,success in [('01',False),('03',True)]:
  folder=root/('compiler-1-explicit-'+attempt);raw=ROOT/'build/connection-dos'/('heap-compiler-1-explicit-'+attempt)
  record=dict(terminal=sha(folder/'TERMINAL.EXE'),interpreter=sha(folder/'ASPECT.EXE'),compiler=sha(folder/'ASPCOMP.EXE'),
   source=sha(raw/'LOGON.ASP'),PRM=sha(raw/'TEST.PRM'),keys=sha(raw/'ACTIONS.KEY'),success=success)
  wire=(raw/'serial.bin').read_bytes();assert wire.count(b'COMPILED\r')==int(success)
  if success:assert(raw/'LOGON.ASX').exists()and record['interpreter']==sha(runner)
  else:assert not(raw/'LOGON.ASX').exists()and b'out of memory'in(raw/'SCREEN.BIN').read_bytes()[::2]
  assert load(raw/'result.json')['cpu']=='8086';heap.append(record);bind(folder);bind(raw)
 for key in('terminal','compiler','source','PRM','keys'):assert heap[0][key]==heap[1][key],key
 assert heap[0]['interpreter']=='c5f6d0d92aab4cb5cda75b17ebccabf1dda42dadde6e83d0adca93ba87a40a62'
 listing=(runner.parent/'ASPECT.map').read_text();segment,offset=re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+__amblksiz\s*$',listing,re.M|re.I)[0]
 image=runner.read_bytes();header=struct.unpack_from('<H',image,8)[0]*16
 assert struct.unpack_from('<H',image,header+int(segment,16)*16+int(offset,16))[0]==512
 assert re.search(r'^STACK\s+STACK\s+DGROUP\s+\S+\s+00002000\s*$',listing,re.M)
 capture(runner.parent/'ASPECT.map')
 for name in['standalone/record_hook_lookup.py','standalone/hook_lookup_fixtures.py','standalone/test_hook_lookup_dos.py','standalone/prove_hook_lookup_source.py']:sources[name]=sha(ROOT/name)
 native=ROOT/'docs/validation/hook-lookup-native.json'
 native_record=load(native);assert native_record['original_sha256']==linked['original_inputs']['analysis/pcplus-originals/PCPLUS-main-2.01.EXE']
 result.update(lookup_cases=lookups,linked_policy=dict(cases=28,bounds=14,native_deviations=2,original_inputs=linked['original_inputs']),
  register_recovery=register,interpreter_heap_growth_control=heap,interpreter_CRT_growth_quantum=512,
  native_evidence_sha256=sha(native),scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS helper lookup:',len(lookups),'DOS targets,28 native-policy/14 bounds,',len(register),'register workflows; composed guards/BBS and11 source products')
if __name__=='__main__':main()
