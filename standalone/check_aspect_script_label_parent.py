#!/usr/bin/env python3
"""Actual parent bridge/label transaction/STATUS; explicit scalar child endpoint."""
import json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_status_live as status
class Parent(status.Status):
 def __init__(self,label=b'NEXT.ASX',error=0):
  super().__init__();self.pulls=[];self.callback_error=error
  self.put('terminal_program_kind',4);self.put('process_psp',0x1000)
  self.memory=json.loads((status.BINARY.parent/'manifest.json').read_text())['memory_layout']
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
  self.uc.mem_write(0x5fff0,b'M'+struct.pack('<HH',0x6000,0x2000)+b'\0'*11)
  self.uc.mem_write(0x63000,struct.pack('<5H',0x5243,4,1,0x2000,0x6200))
  self.uc.mem_write(0x65000,label+b'\0'+b'\0'*13)
  # Explicit child callback: OP7 reads scalar bytes; OP4 returns typed error.
  self.uc.mem_write(0x64000,bytes.fromhex('9c 53 83 f8 07 75 09 31 c0 2e 8a 87 00 30 eb 03 31 c0 90 5b 9d cb'))
 def boundary(self,u,address,size,unused):
  if address==self.symbols['_aspect_render_admit']:
   # Admission policy is independently exercised; do not substitute STATUS,
   # label validation, renderer/bridge mechanics or client MCB validation.
   ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)
   ip=int.from_bytes(u.mem_read(ss*16+sp,2),'little')
   u.reg_write(UC_X86_REG_AX,0);u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
  if address==0x64000:
   op=u.reg_read(UC_X86_REG_AX);self.pulls.append((op,u.reg_read(UC_X86_REG_BX)))
   if op==4 and self.callback_error:
    # Same explicit callback boundary with an injected typed error.
    u.reg_write(UC_X86_REG_AX,self.callback_error)
    ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP)
    ip,cs=struct.unpack('<HH',u.mem_read(ss*16+sp,4))
    u.reg_write(UC_X86_REG_SP,sp+4);u.reg_write(UC_X86_REG_CS,cs);u.reg_write(UC_X86_REG_IP,ip)
 def interrupt(self,u,n,unused):
  assert n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62
  u.reg_write(UC_X86_REG_BX,0x6000)
 def far(self,name,ax=0,bx=0,child=False):
  u=self.uc;target=self.symbols[name]
  segment=self.base_segment+next(s['relative_segment'] for s in self.memory['code_segments'] if self.base+s['relative_segment']*16<=target<self.base+s['relative_segment']*16+s['bytes'])
  ds=0x6200 if child else self.ds
  sp=0xe000 if child else self.offset('terminal_stack_top')-4
  for reg,value in [(UC_X86_REG_CS,segment),(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,ax),(UC_X86_REG_BX,bx),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,ds),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
  u.mem_write(ds*16+sp,struct.pack('<HH',self.return_offset,self.base_segment))
  self.returned=False;u.emu_start(target,0,count=500000);assert self.returned,name
  for reg,value in [(UC_X86_REG_DS,ds),(UC_X86_REG_SS,ds),(UC_X86_REG_SP,sp+4),(UC_X86_REG_BP,0xbabe)]:assert u.reg_read(reg)==value,(name,reg,u.reg_read(reg),value)
  return u.reg_read(UC_X86_REG_AX)
 def begin(self):
  assert self.far('terminal_render_prepare')==0
  token=self.get('_script_render_token');self.uc.mem_write(0x63004,struct.pack('<H',token))
  assert self.far('resident_bridge_entry',0,0x1000,True)==0
 def label(self):return bytes(self.uc.mem_read(self.symbols['terminal_script_label'],13))
def main():
 cases=[]
 for label in [b'A.ASX',b'12345678.ASX',b'\x82.ASX']:
  for duplex in [0,1,255,65535]:
   m=Parent(label);m.begin();assert m.far('resident_bridge_entry',6,duplex,True)==0
   assert m.get('terminal_script_label_valid')==1 and m.label()==label+b'\0'*(13-len(label))
   assert m.row().startswith(b' '+label)
   assert bytes(m.uc.mem_read(m.symbols['_command_menu_script'],19))==b'C:\\TOOLS\\CHECK.ASX\0'
   assert [v for op,v in m.pulls if op==7]==list(range(len(label)+1))
   assert m.get('modes_value_1d1a')==0
   assert m.far('terminal_render_revoke')==0 and not m.get('terminal_script_label_valid')
   assert m.run()==0 and m.row().startswith(b' CHECK.ASX')
   cases.append(dict(name='accepted-'+label.hex()+'-'+str(duplex),passed=True))
 for label in [b'',b'.ASX',b'X.ASP',b'A..ASX',b'A/B.ASX',b'C:X.ASX',b'A\\B.ASX',b'A\x01.ASX',b'123456789.ASX',b'A.asx',b'X'*13]:
  m=Parent(label);m.begin();before=m.label()
  assert m.far('resident_bridge_entry',6,65535,True)==7,label
  assert not m.get('terminal_script_label_valid') and m.label()==before and not m.inputs
  cases.append(dict(name='reject-'+label.hex(),passed=True))
 for error in [10,14,65535]:
  m=Parent(error=error);m.begin();assert m.far('resident_bridge_entry',6,65535,True)==(error if error<=14 else 10)
  assert not m.get('terminal_script_label_valid') and not m.inputs
  cases.append(dict(name='callback-error-'+str(error),passed=True))
 m=Parent();m.begin();m.put('terminal_script_label_valid',1);m.uc.mem_write(m.symbols['terminal_script_label'],b'OLD.ASX'+b'\0'*6)
 before=m.label();m.put('terminal_baud_low',12345)
 assert m.far('resident_bridge_entry',6,65535,True)==3
 assert m.get('terminal_script_label_valid')==1 and m.label()==before and not m.inputs
 cases.append(dict(name='drawing-preflight-rollback',passed=True))
 m=Parent();m.begin()
 m.uc.mem_write(m.symbols['_script_handoff']+22,b'\x01\0')
 assert m.far('resident_bridge_entry',6,65535,True)==14 and not m.pulls
 cases.append(dict(name='returned-UART-rejected-before-callback',passed=True))
 m=Parent();m.begin();assert m.far('resident_bridge_entry',6,256,True)==7 and not m.pulls
 cases.append(dict(name='duplex-rejected-before-callback',passed=True))
 report=dict(passed=True,cases=cases,binary_sha256=status.hashlib.sha256(status.BINARY.read_bytes()).hexdigest(),checker_sha256=status.hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual parent resident bridge, client MCB validator, scalar label parser, rollback and native STATUS rendering. Explicit child callback, DOS62, MSR and independent admission-success boundary; actual DOS interoperability separately required.')
 (status.BINARY.parent/'script-label-parent-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Script label parent',len(cases),'cases PASS')
if __name__=='__main__':main()
