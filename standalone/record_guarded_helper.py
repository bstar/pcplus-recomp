#!/usr/bin/env python3
"""Bind current guarded-helper products to raw DOS, BBS and source evidence."""
import argparse,json,re,struct,sys
from pathlib import Path
from build_guarded_helper import ROOT,GUARDED,CONTROL,LOOKUP
from prove_guarded_helper_source import sha
from check_guarded_helper_usage_dos import usage
from test_hook_apply_dos import FIELDS
from test_terminal_cancel_dos import CASES
from record_hook_bbs import verify_case
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
 p.add_argument('--lookup',action='store_true')
 p.add_argument('--trap-label',required=True);p.add_argument('--cancel-label',required=True)
 p.add_argument('--sync-label',required=True);p.add_argument('--enigma-label',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve()
 assert root.is_relative_to(ROOT/'build')
 sources={};artifacts={}
 def merge(mapping):
  for name,digest in mapping.items():
   assert sha(ROOT/name)==digest and(name not in sources or sources[name]==digest),name
   sources[name]=digest
 def capture(path):
  assert path.is_relative_to(ROOT/'build');artifacts[str(path.relative_to(ROOT))]=sha(path)
 def bind(folder):
  for path in folder.rglob('*'):
   if path.is_file():capture(path)
 def current(folder,leaf):
  base=ROOT/'build'/folder;m=load(base/'manifest.json');assert not m.get('original_inputs')
  assert sha(base/leaf)==m['binary_sha256'];merge(m['sources']);capture(base/leaf);capture(base/'manifest.json')
  return base/leaf,m
 selected=LOOKUP if a.lookup else GUARDED
 terminal,m=current(selected,'TERMINAL.EXE');control,c=current(CONTROL,'TERMINAL.EXE')
 runner,_=current('aspect-register-parent','ASPECT.EXE');compiler,_=current('aspect-compiler-dos','ASPCOMP.EXE')
 assert sha(control)=='a024383fa0171baa88ca317c27b01461f14abd2c9c33cec364975c27a5483679'
 assert m['terminal_traps']and m['terminal_exit_guard']and m['experimental_hook_apply']and m['terminal_trap_probe']is None
 memory=m['memory_layout'];assert memory['near_bytes']==(64096 if a.lookup else 64064)and memory['near_spare_bytes']==(1440 if a.lookup else 1472)
 assert bool(m.get('experimental_hook_lookup'))==a.lookup
 assert memory['far_usage_bytes']==1493 and memory['far_usage_DS_restore_verified']
 listing=(terminal.parent/'terminal.map').read_text();assert re.search(r'^STACK\s+STACK\s+DGROUP\s+\S+\s+00002000\s*$',listing,re.M)
 assert usage(terminal.parent)==usage(control.parent)
 trap_root=ROOT/'build/terminal-trap-tests'/a.trap_label;trap=load(trap_root/'result.json')
 assert trap['passed']and {r['case']for r in trap['cases']}=={str(m)+str(b)for m in range(5)for b in(0,1)}
 merge(trap['sources']);trap_cases=[]
 for r in trap['cases']:
  mode,initial=r['mode'],r['initial_break'];folder=trap_root/r['case'];binary,probe=current(selected+'-probe-'+str(mode),'TERMINAL.EXE')
  assert r['passed']and all(r['checks'].values())and r['cpu']=='8086'and r['child_sha256']==sha(binary)
  assert r['parent_sha256']==sha(folder/'TROBS.EXE')and r['startup_child_sha256']==sha(folder/'PRMEDIT.EXE')
  w=struct.unpack('<31H',(folder/'TRAPWIT.BIN').read_bytes());child=struct.unpack('<11H',(folder/'CHILTRAP.BIN').read_bytes())
  assert w[:2]==(0x5452,mode)and w[2]>=16 and w[3]==(4 if mode==4 else 0)and w[5]==0
  assert w[4]==(2 if mode==3 else 1 if mode in(1,2)else 0)and w[6]==initial and w[7]==(0 if mode==4 else initial)
  assert w[30]==1 and child[:4]==(0x4354,w[2],2,0)and child[4:10]==w[12:18]and child[10]==initial
  if mode!=4:assert w[12:18]==w[18:24]
  else:assert w[18:20]==w[24:26]and w[28]==0 and w[29]>0
  if mode==2:assert w[11]&255==3
  if mode==3:assert(w[8],w[9],w[11])==(0x0801,12,0x0803)
  assert 'failures=0' in(folder/'TRAPPAR.OUT').read_text()
  trap_cases.append(dict(case=r['case'],witness=list(w),parent_report=r['parent_report']))
 bind(trap_root)
 cancel_root=ROOT/'build/terminal-cancel-tests'/a.cancel_label;cancel=load(cancel_root/'result.json')
 assert cancel['passed']and {r['case']for r in cancel['cases']}==set(CASES)and cancel['binary_sha256']==sha(terminal)
 merge(cancel['sources']);cancellations=[]
 for r in cancel['cases']:
  folder=cancel_root/r['case'];w=struct.unpack('<16H',(folder/'CANCEL.BIN').read_bytes())
  assert r['passed']and all(r['checks'].values())and r['cpu']=='8086'
  assert w[0]==0xca16 and w[1]==16 and w[3:5]==(1,0)and w[5]<18 and w[6:9]==(1,0,1)and w[12]==1
  assert r['marker'].rstrip('+').encode()in(folder/'CANCEL.VID').read_bytes()
  assert(folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  if r['case']=='receive-partial':assert w[15]==1 and not(folder/'RECV.BIN').exists()and not(folder/'PCRX.$$$').exists()
  cancellations.append(dict(case=r['case'],witness=list(w)))
 bind(cancel_root)
 helpers=[];ownership=[]
 for port in(1,2):
  for kind,modes in [('apply',range(13)),('online',(0,1,2,3,5,6,9,10)),('ownership',(0,1))]:
   for mode in modes:
    folder=root/f'final-{kind}-{port}-{mode:02}';r=load(folder/'result.json');merge(r['sources'])
    assert r['passed']and r['mode']==mode and r['port']==port and r['binary_sha256']==sha(terminal)
    assert r['online']==(kind!='apply')and sha(folder/'APPLYCH.EXE')==r['helper_sha256']
    assert(folder/'COUNT.BIN').read_bytes()==struct.pack('<H',3)
    before=[(folder/f'B{i}.BIN').read_bytes()for i in range(3)];after=[(folder/f'A{i}.BIN').read_bytes()for i in range(3)]
    assert all(len(x)==2094 for x in before+after)
    status={1:107,2:105,3:106,8:408,9:107,10:305}.get(mode,0)
    assert r['status']==status and r['committed']==(status==0)
    assert before[1]==(after[0]if status==0 else before[0])and before[2]==after[1]==before[1]
    fields=FIELDS+(r.get('trap_fields')or[])
    for i in range(3):
     raw=(folder/f'S{i}.BIN').read_bytes();assert sha(folder/f'S{i}.BIN')==r['snapshots'][i]
     assert len(raw)==sum(size for _,size in fields)
     # Snapshot begins with the source-bound register owner; later children
     # must see the accepted bank and the correct commit/rejection epoch.
     if i:
      assert raw[904:1734]==before[i][:830]and struct.unpack_from('<H',raw)[0]==0
      assert struct.unpack_from('<H',raw,4)[0]==(i if status==0 else i-1)
     if kind=='ownership':
      offset=sum(size for _,size in FIELDS);trap_words=struct.unpack_from('<13H',raw,offset)
      valid=struct.unpack_from('<H',raw,offset+26)[0];guard=struct.unpack_from('<5H',raw,offset+28)
      assert trap_words[:2]==(2,0)and trap_words[2]==guard[0]and trap_words[4]==1 and trap_words[11:]==(0,0)
      assert valid==1 and guard[0]>=16 and guard[1]==memory['retained_parent_paragraphs']and guard[2:]==(0,0,65535)
    if kind=='ownership':assert r['trap_ownership'][0]==r['trap_ownership'][1]==r['trap_ownership'][2];ownership.append(dict(port=port,mode=mode,witness=r['trap_ownership']))
    else:helpers.append(dict(port=port,mode=mode,online=r['online'],committed=r['committed'],status=r['status']))
    assert(folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
    if not r['online']:assert(folder/'BEFORE2.BIN').read_bytes()==(folder/'AFTER2.BIN').read_bytes()
    else:
     assert r['peer']['passed']and all(r['peer']['checks'].values())and r['peer']['cpu']=='8086'
     wire=(folder/'serial.bin').read_bytes();assert wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
    bind(folder)
 nested=[]
 for port in(1,2):
  for case in('explicit','fallback','chain','rejected'):
   folder=root/f'final-compiler-{port}-{case}';r=load(folder/'result.json');merge(r['sources'])
   assert r['passed']and r['port']==port and r['case']==case
   assert r['products']=={'TERMINAL.EXE':sha(terminal),'ASPECT.EXE':sha(runner),'ASPCOMP.EXE':sha(compiler)}
   assert r['connection']['passed']and r['connection']['cpu']=='8086'and all(r['connection']['checks'].values())
   label=r['connection']['case'];assert re.fullmatch('[A-Za-z0-9_-]+',label)
   raw=ROOT/'build/connection-dos'/label;wire=(raw/'serial.bin').read_bytes()
   assert wire.count(b'COMPILED\r')==(case!='rejected')and wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
   assert(raw/'BEFORE.BIN').read_bytes()==(raw/'AFTER.BIN').read_bytes()
   for path in raw.glob('*.ASP'):
    if case=='rejected':assert not path.with_suffix('.ASX').exists()
    else:assert path.with_suffix('.ASX').read_bytes()==compile_source(path.read_bytes().decode('cp437'))
   for name,digest in r['artifacts'].items():assert sha(ROOT/name)==digest;artifacts[name]=digest
   bind(folder);nested.append(dict(port=port,case=case))
 u=load(root/'final-usage/result.json');assert u['passed']and u['binary_sha256']==sha(terminal);merge(u['sources'])
 assert(root/'final-usage/HELP.TXT').read_bytes()==(root/'final-usage/INVALID.TXT').read_bytes()==usage(terminal.parent);bind(root/'final-usage')
 proof=load(root/'final-source/result.json');assert proof['passed']and not proof['original_inputs']and len(proof['products'])==(11 if a.lookup else 9);merge(proof['sources'])
 for folder,digest in proof['products'].items():
  leaf='ASPECT.EXE'if folder in('aspect-register-parent','aspect-runner')else'ASPCOMP.EXE'if folder=='aspect-compiler-dos'else'TERMINAL.EXE'
  assert sha(ROOT/'build'/folder/leaf)==digest
 capture(root/'final-source/result.json');capture(root/'final-source/build.log')
 bbs=[]
 for server,label,delay in [('synchronet',a.sync_label,0),('enigma',a.enigma_label,30)]:
  r=verify_case(server,label,'accept',delay,terminal,runner,expected_cpu='386');assert r['source_compilation']and r['editor_passed']
  stage=ROOT/'build/bbs-lab/script-login'/label;run=ROOT/'build/bbs-lab/results'/server/label
  reported=load(stage/'checks.json')
  for name,digest in reported['artifacts'].items():assert sha(ROOT/name)==digest,name
  observed=struct.unpack_from('<4H',(run/'SCRIPT.BIN').read_bytes());assert observed[0]==0x4d43 and observed[1]&6==0 and observed[2]>0 and observed[3]>=0xa000
  assert reported['observer_high']and reported['observer_segment']==observed[3];merge(r.pop('sources'))
  for name,digest in r.pop('artifacts').items():assert sha(ROOT/name)==digest;artifacts[name]=digest
  bbs.append(dict(**r,observer_segment=observed[3],cpu='386'))
 for name in ['standalone/record_guarded_helper.py','standalone/build_guarded_helper.py','standalone/record_hook_bbs.py','Makefile']:sources[name]=sha(ROOT/name)
 result=dict(passed=True,terminal_sha256=sha(terminal),unchanged_control_sha256=sha(control),memory=memory,stack_bytes=8192,
  trap_cases=trap_cases,cancellations=cancellations,helper_cases=helpers,helper_trap_ownership=ownership,nested_compiler=nested,BBS=bbs,
  source_products=proof['products'],source_files=len(proof['sources']),sources=sources,artifacts=artifacts,
  limitations=['Trap foreground probes and cancellation interrupts are declared stimuli; no physical Ctrl-Break or device-critical fault claim.',
   'BBS source/helper/editor tests use a386 profile and a verified upper-memory observer; bare serial tests use8086.',
   'ENiGMA passes with explicit30ms buffering. Immediate-forwarding and the physical modem remain unverified here.',
   'Additional native parity, complete application gates and card deployment remain open.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS guarded helper:',len(trap_cases),'trap,',len(cancellations),'cancel,',len(helpers),'helper,',len(ownership),'ownership,',len(nested),'compiler,',len(bbs),'BBS;',len(proof['products']),'original-free products')
if __name__=='__main__':main()
