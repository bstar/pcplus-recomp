#!/usr/bin/env python3
"""Actual migrated codec/framing, returned FLAGS and checked compiler imports."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_terminal_ymodem_live import LiveYmodem,metadata,packet
from omf_imports import rename_imports,records,externals
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ymodem-far';OUT.mkdir(parents=True,exist_ok=True)
RENAMES={'__U4D':'config_u4div_service_','__U4M':'config_u4mul_service_'}
REGS=[UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_EFLAGS]
CALLBACKS=['config_u4div_service_','config_u4mul_service_','_config_ym_crc','_config_ym_read','_config_ym_put','_config_ym_unread','_config_ym_poll','_config_ym_progress','_config_bd_begin','_config_bd_open','_config_bd_append','_config_bd_finish','_config_bd_cleanup','_config_bu_begin','_config_bu_read','_config_bu_next','_config_bu_close','_config_bu_abort']
ENTRIES={'_ymodem_run':2,'_batch_header_end':2,'_batch_header_encode':6,'_batch_header_decode':3}

class FarBatch(LiveYmodem):
 def __init__(self,**kw):
  super().__init__(**kw);self.pending=[];self.public_pending={n:[] for n in ENTRIES};self.seen={n:0 for n in CALLBACKS};self.returns={n:0 for n in ENTRIES}
  cdecl={n:int(words) for n,words in re.findall(r'^CONFIG_CDECL\s+(\w+),\s*\w+,\s*(\d+)',(ROOT/'src/terminal/config_abi.inc').read_text(),re.M)}
  # Observe RETF after copied arguments and saved BP have been released.
  self.resident={self.symbols[n+'_resident']+(10+3*cdecl[n] if n in cdecl else 3):n for n in CALLBACKS}
  self.services={self.symbols[n if n.endswith('_') else n+'_service']+5:n for n in CALLBACKS}
  self.near_returns={self.symbols[n]+3+count*3+5+4:n for n,count in ENTRIES.items()}
  self.config_cs=self.symbols['terminal_config_code_start']//16
  self.c_returns={(self.symbols[n+'_far']-self.config_cs*16)+3+count*3+3:n for n,count in ENTRIES.items()}
  self.uc.hook_add(UC_HOOK_CODE,self.watch)
 def snapshot_regs(self):return tuple(self.uc.reg_read(r) for r in REGS)
 def watch(self,u,address,size,_):
  if address in self.resident:
   assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
   self.pending.append((self.resident[address],self.snapshot_regs(),u.reg_read(UC_X86_REG_SP)))
  if address in self.services:
   name,values,sp=self.pending.pop();assert name==self.services[address]
   assert self.snapshot_regs()==values,(name,'register/FLAGS changed across return')
   assert u.reg_read(UC_X86_REG_SP)==sp+4,(name,'far frame not released')
   self.seen[name]+=1
  if u.reg_read(UC_X86_REG_CS)==self.config_cs and u.mem_read(address,1)==b'\xc3':
   at=(u.reg_read(UC_X86_REG_SS)<<4)+u.reg_read(UC_X86_REG_SP)
   ret=struct.unpack('<H',u.mem_read(at,2))[0]
   if ret in self.c_returns:
    name=self.c_returns[ret]
    self.public_pending[name].append((u.reg_read(UC_X86_REG_EFLAGS),u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX),u.reg_read(UC_X86_REG_SP)))
  if address in self.near_returns:
   name=self.near_returns[address];flags,ax,dx,sp=self.public_pending[name].pop()
   assert (u.reg_read(UC_X86_REG_EFLAGS),u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX))==(flags,ax,dx),name
   assert u.reg_read(UC_X86_REG_SP)==sp+10+4*ENTRIES[name],name
   self.returns[name]+=1
 def checked(self):
  assert not self.pending and not any(self.public_pending.values())

def record(kind,payload):
 head=struct.pack('<BH',kind,len(payload)+1)+payload
 return head+bytes([-sum(head)&255])

def main():
 groups=[]
 def done(name,n):groups.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 before=(ROOT/'build/terminal/batch-header-compiler.obj').read_bytes();after=(ROOT/'build/terminal/batch_header.obj').read_bytes()
 normalized,counts=rename_imports(before,RENAMES);assert normalized==after and counts=={'__U4D':2,'__U4M':1}
 restored,back=rename_imports(after,{v:k for k,v in RENAMES.items()});assert restored==before and sorted(back.values())==[1,2]
 asm=[]
 for filename,label in [('batch-header-compiler.obj','compiler'),('batch_header.obj','normalized')]:
  path=OUT/(label+'.asm')
  subprocess.run(['wdis','-a','-l='+str(path),str(ROOT/'build/terminal'/filename)],check=True,stdout=subprocess.DEVNULL)
  asm.append(path.read_text())
 replaced=asm[1]
 for old,new in RENAMES.items():replaced=replaced.replace(new,old)
 assert asm[0]==replaced,'Independent disassembler found a change beyond helper imports'
 done('compiler-OMF-normalization-roundtrip-and-independent-wdis-equivalence',3)
 fixture=record(0x80,b'\x04TEST')+record(0x8c,b'\x05__U4D\x81\x23\x05__U4M\0')+record(0xb4,b'\x05__U4D\0')+record(0x88,b'\0\0__U4D')+record(0x8a,b'\0')
 fixed,found=rename_imports(fixture,RENAMES);assert found=={'__U4D':1,'__U4M':1}
 assert externals(records(fixed)[1][1])==[(b'config_u4div_service_',b'\x81\x23'),(b'config_u4mul_service_',b'\0')]
 assert records(fixture)[2:]==records(fixed)[2:]
 invalid=[b'',fixture[:-1],fixture+b'\x80',bytes([fixture[0]^1])+fixture[1:],record(0x80,b'\x04TEST')+record(0x8c,b'\x05__U4D\x80')+record(0x8a,b'\0'),record(0x80,b'\x04TEST')+record(0x8c,b'\0\0')+record(0x8a,b'\0'),fixture+fixture]
 for bad in invalid:
  try:rename_imports(bad,RENAMES)
  except ValueError:pass
  else:raise AssertionError('Malformed OMF accepted')
 for names in [{},{'absent':'local_'},{'__U4D':'__U4D'},{'__U4D':'SAME','__U4M':'SAME'},{'__U4D':'__U4M'},{'__U4D':'X'*256}]:
  try:rename_imports(fixture,names)
  except ValueError:pass
  else:raise AssertionError('Invalid import mapping accepted')
 done('two-byte-type-index-local-symbols-data-and-thirteen-invalid-objects-or-mappings',14)
 values={0,1,9,10,127,128,255,256,65535,65536,0x7fffffff,0x80000000,0xffffffff}
 values.update(1<<i for i in range(32));values.update((1<<i)-1 for i in range(1,33))
 seed=0x426f6172
 for _ in range(128):seed=(1664525*seed+1013904223)&0xffffffff;values.add(seed)
 m=FarBatch();name=m.scratch(b'DATA.BIN\0',6000);block=m.scratch(b'\xa5'*128,5400);result=m.scratch(b'\xcc'*36,5000)
 for value in sorted(values):
  assert m.call('_batch_header_encode',[name,13,value&65535,value>>16,block,128])==0
  assert bytes(m.uc.mem_read(m.data_base+block,128))==metadata('DATA.BIN',value)
  assert m.call('_batch_header_decode',[block,128,result])==0
  expected=struct.pack('<13sBHIIIIHH',b'DATA.BIN',1,1,value,0,0,0,0,0)
  assert bytes(m.uc.mem_read(m.data_base+result,36))==expected,value
 assert m.call('_batch_header_end',[block,128])==0
 assert bytes(m.uc.mem_read(m.data_base+block,128))==bytes(128)
 m.checked();seen=dict(m.seen);returns=dict(m.returns)
 done('two-word-end-header-entry-clears-entire-block',1)
 assert seen['config_u4div_service_'] and seen['config_u4mul_service_']
 done('six-word-DWORD-encoder-and-three-word-decoder-vs-independent-decimal-reference',len(values)*2)
 # Octal DWORD boundaries exercise the decoder's multiplication/division paths.
 for text,expected_status in [(b'4294967295 37777777777 37777777777 37777777777',0),(b'4294967296',4),(b'0 40000000000',4)]:
  raw=(b'DATA.BIN\0'+text+b'\0').ljust(128,b'\0');m.uc.mem_write(m.data_base+block,raw)
  assert m.call('_batch_header_decode',[block,128,result])==expected_status
 m.checked();seen=dict(m.seen);returns=dict(m.returns)
 done('decimal-and-octal-DWORD-maximum-and-overflow-boundaries',3)
 for sending,fault,want in [(False,None,0),(True,None,0),(False,'write',7),(True,'read',7)]:
  live=FarBatch(sending=sending,fault=fault,peer=True)
  assert live.run_engine()==want,(sending,fault)
  live.checked()
  for n,count in live.seen.items():seen[n]+=count
  for n,count in live.returns.items():returns[n]+=count
 assert all(seen.values()),seen
 assert all(returns.values()),returns
 done('real-UART-CRC-framing-file-owners-and-all-eighteen-callback-return-frames',4)
 manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
 # Exact savings belong to the historical migration report; later features
 # consume that capacity. Keep placement/near ABI limits independently checked.
 assert manifest['memory_layout']['ymodem_far_code_verified']
 assert manifest['memory_layout']['near_bytes']<65536
 assert manifest['memory_layout']['resident_code_bytes']<65536
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
  inputs=sum(g['inputs'] for g in groups),cases=groups,compiler_import_counts=counts,callback_returns_observed=seen,public_entry_returns_observed=returns,
  compiler_object_sha256=hashlib.sha256(before).hexdigest(),normalized_object_sha256=hashlib.sha256(after).hexdigest(),
  sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['standalone/check_ymodem_far_live.py','standalone/omf_imports.py','standalone/check_terminal_ymodem_live.py','src/terminal/config_abi.inc','src/transfer/ymodem.c','src/transfer/batch_header.c']},
  scope='Actual linked migrated codec/framing and source-owned adapters. Independent decimal/CRC peers, actual register/FLAGS and stack observations at C/near/far returns. Compiler object import normalization checked by inverse transform and independent Open Watcom disassembly; malformed records fail closed. Only DOS/BIOS/UART boundaries modeled; actual DOS and source-only rebuild evidence remain separate.')
 (ROOT/'build/terminal/ymodem-far-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('YMODEM far-code checks passed',result['inputs'])
if __name__=='__main__':main()
