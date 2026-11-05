#!/usr/bin/env python3
"""Execute actual banked viewer owner/DOS boundary with modeled errors and real claims."""
import argparse,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_path_session import ROOT,sha

class Owner(DosImage):
 def __init__(self,binary,fault=''):
  super().__init__(binary,binary.with_name('VIEWFILE.map'))
  self.entries={n:(self.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('VIEWFILE.map').read_text(),re.M|re.I)}
  self.fault=fault;self.calls=[];self.position=0;self.opened=False
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.mem_write(self.data_base+0xb000,b'data.bin\0'+bytes(55))
  self.uc.mem_write(0x80300,b'\xa5'*288)
 def carry(self,error):
  flags=self.uc.reg_read(UC_X86_REG_EFLAGS)
  self.uc.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)
  self.uc.reg_write(UC_X86_REG_AX,error)
 def interrupt(self,u,number,data):
  assert number==0x21
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;ds=u.reg_read(UC_X86_REG_DS);ss=u.reg_read(UC_X86_REG_SS)
  bx=u.reg_read(UC_X86_REG_BX);dx=u.reg_read(UC_X86_REG_DX);cx=u.reg_read(UC_X86_REG_CX)
  op='canonical' if ax==0x6000 else 'attributes' if ax==0x4300 else 'open' if ah==0x3d else 'device' if ax==0x4400 else 'read' if ah==0x3f else 'seek' if ax==0x4200 else 'close' if ah==0x3e else None
  assert op,(hex(ax),'unexpected DOS operation');self.calls.append(op)
  assert ss==self.ds and (ds==ss or op=='read')
  error={'canonical-error':('canonical',3),'attributes-error':('attributes',5),'open-error':('open',5),
   'device-error':('device',6),'read-error':('read',5),'seek-error':('seek',25),'close-error':('close',6)}.get(self.fault)
  if self.fault=='read-close-error' and op in ['read','close']:error=(op,5 if op=='read' else 6)
  if error and error[0]==op:
   if op=='read':u.mem_write(ds*16+dx,b'!'*cx)
   self.carry(error[1]);return
  self.carry(0)
  if op=='canonical':
   assert u.reg_read(UC_X86_REG_ES)==ss and cx==0
   source=bytes(u.mem_read(ds*16+u.reg_read(UC_X86_REG_SI),64)).split(b'\0',1)[0]
   assert source==b'data.bin'
   value=b'D:\\CON.TXT\0' if self.fault=='canonical-device' else b'D:\\DATA.BIN\0'
   u.mem_write(ss*16+u.reg_read(UC_X86_REG_DI),value)
  elif op=='attributes':
   assert bytes(u.mem_read(ds*16+dx,12))==b'D:\\DATA.BIN\0'
   u.reg_write(UC_X86_REG_CX,0x10 if self.fault=='directory' else 0x08 if self.fault=='volume' else 0x01)
  elif op=='open':
   assert ax==0x3da0 and not self.opened
   assert bytes(u.mem_read(ds*16+dx,12))==b'D:\\DATA.BIN\0'
   self.opened=True;self.position=0;u.reg_write(UC_X86_REG_AX,0xffff if self.fault=='invalid-handle' else 7)
  elif op=='device':
   assert bx==7 and self.opened;u.reg_write(UC_X86_REG_DX,0x80 if self.fault=='character-device' else 0)
  elif op=='read':
   assert bx==7 and self.opened and cx<=256
   u.mem_write(ds*16+dx,bytes((self.position+i)&255 for i in range(cx)))
   self.position+=cx;u.reg_write(UC_X86_REG_AX,cx+1 if self.fault=='read-too-many' else cx)
  elif op=='seek':
   assert bx==7 and self.opened;self.position=(cx<<16)|dx
   result=self.position+1 if self.fault=='seek-wrong' else self.position
   u.reg_write(UC_X86_REG_AX,result&65535);u.reg_write(UC_X86_REG_DX,result>>16)
  elif op=='close':assert bx==7 and self.opened;self.opened=False
 def bank(self,name,args=()):
  u=self.uc;seg,off=self.entries['_viewer_file_'+name]
  for r,v in [(UC_X86_REG_CS,seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
    (UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),
    (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:u.reg_write(r,v)
  words=[self.return_offset,self.code_segment]+list(args);sp=0xe000-2*len(words)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;u.emu_start(seg*16+off,0,count=1000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4,(name,'return/stack')
  for r,v in [(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),
    (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert u.reg_read(r)==v,(name,'ABI')
  return u.reg_read(UC_X86_REG_AX)
 def snapshot(self):
  assert self.bank('inspect',[0xb100])==0
  raw=bytes(self.uc.mem_read(self.data_base+0xb100,84));return struct.unpack_from('<8HL',raw),raw[20:].split(b'\0',1)[0]
 def open(self):return self.bank('open',[0xb000,0xb300])
 def read(self,count=256):
  self.uc.mem_write(self.data_base+0xb200,b'\xaa\xaa')
  status=self.bank('read',[0x310,0x8000,count,0xb200])
  return status,int.from_bytes(self.uc.mem_read(self.data_base+0xb200,2),'little')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 rows=[]
 faults=[('canonical-error',4,3,0),('canonical-device',4,0,0),('attributes-error',6,5,0),('directory',6,0,0),('volume',6,0,0),
  ('open-error',7,5,0),('device-error',8,6,1),('character-device',8,0,1)]
 for fault,want,error,closes in faults:
  m=Owner(binary,fault);assert m.open()==want
  s,path=m.snapshot();assert s[0:3]==(3,want,error) and s[6:9]==(65535,0,0)
  assert m.calls.count('close')==closes
  calls=m.calls[:];assert m.bank('close')==want and m.calls==calls
  assert m.uc.mem_read(m.symbols['_capture_reservation']+8,2)==b'\0\0'
  rows.append(dict(case=fault,status=want,DOS_calls=m.calls,closed=closes,passed=True))
 for fault,want,error,operation in [('read-error',9,5,'read'),('read-too-many',14,0,'read'),('seek-error',10,25,'seek'),('seek-wrong',14,0,'seek')]:
  m=Owner(binary,fault);assert m.open()==0
  if operation=='read':assert m.read()==(want,0xaaaa)
  else:assert m.bank('seek',[69696&65535,69696>>16])==want
  s,path=m.snapshot();assert s[0:3]==(2,want,error) and s[6:9]==(7,1,0)
  calls=m.calls[:];assert m.read()==(3,0xaaaa) and m.bank('seek',[0,0])==3 and m.calls==calls
  assert m.bank('close')==want and m.calls.count('close')==1
  assert m.snapshot()[0][6:8]==(65535,0)
  calls=m.calls[:];assert m.bank('close')==want and m.calls==calls
  rows.append(dict(case=fault,status=want,DOS_calls=m.calls,passed=True))
 for fault in ['close-error','read-close-error','release-error','invalid-handle']:
  m=Owner(binary,fault);opened=m.open()
  if fault=='invalid-handle':assert opened==14
  else:
   assert opened==0
   if fault=='read-close-error':assert m.read()==(9,0xaaaa)
   if fault=='release-error':m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\1\0')
   assert m.bank('close')==({'close-error':11,'read-close-error':9,'release-error':12}[fault])
  s,path=m.snapshot();assert s[0]==4 and s[7]==1 and path==b'D:\\DATA.BIN'
  assert s[3]==(6 if fault in ['close-error','read-close-error'] else 0)
  assert s[5]==(2 if fault=='release-error' else 0)
  assert m.calls.count('close')==(0 if fault=='invalid-handle' else 1)
  calls=m.calls[:];before=bytes(m.uc.mem_read(m.symbols['_viewer_file_storage'],90))
  assert m.bank('close')==13 and m.open()==13 and m.read()==(13,0xaaaa) and m.bank('seek',[0,0])==13
  assert m.calls==calls and bytes(m.uc.mem_read(m.symbols['_viewer_file_storage'],90))==before
  rows.append(dict(case=fault,quarantined=True,DOS_calls=m.calls,first_status=s[1],close_error=s[3],release_error=s[5],passed=True))
 m=Owner(binary);m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\1\0');assert m.open()==5
 assert m.calls==['canonical'] and m.snapshot()[0][4]==2
 rows.append(dict(case='reservation-busy-before-open',passed=True,DOS_calls=m.calls))
 m=Owner(binary);assert m.open()==0
 assert m.bank('seek',[69696&65535,69696>>16])==0 and m.read()==(0,256)
 assert bytes(m.uc.mem_read(0x80310,256))==bytes((69696+i)&255 for i in range(256))
 assert m.snapshot()[0][8]==69952 and m.bank('close')==0
 assert bytes(m.uc.mem_read(0x80300,16))==b'\xa5'*16 and bytes(m.uc.mem_read(0x80410,16))==b'\xa5'*16
 rows.append(dict(case='far-buffer-32-bit-position',passed=True,DOS_calls=m.calls))
 m=Owner(binary);assert m.open()==0
 state=m.symbols['_viewer_file_storage'];ss,so=m.entries['_viewer_file_storage']
 recipes=[('count257',[0x310,0x8000,257,0xb200]),('buffer-wrap',[0xffff,0x8000,2,0xb200]),
  ('over-1MB',[0x10,0xffff,1,0xb200]),('null-buffer',[0,0,1,0xb200]),
  ('owner-alias',[so+16,ss-1,1,0xb200]),('output-overlap',[0xb210,m.ds-1,1,0xb200])]
 for name,args in recipes:
  before=bytes(m.uc.mem_read(state,90));calls=m.calls[:];m.uc.mem_write(m.data_base+0xb200,b'\xaa\xaa')
  assert m.bank('read',args)==1 and m.calls==calls and bytes(m.uc.mem_read(state,90))==before
  assert bytes(m.uc.mem_read(m.data_base+0xb200,2))==b'\xaa\xaa'
  rows.append(dict(case=name,argument_preserves_owner_output=True,passed=True))
 for busy in [1]:
  m.uc.mem_write(state+4,struct.pack('<H',busy));calls=m.calls[:]
  assert m.open()==2 and m.read()==(2,0xaaaa) and m.bank('seek',[0,0])==2 and m.bank('close')==2 and m.bank('inspect',[0xb100])==2 and m.calls==calls
  rows.append(dict(case='reentrant-owner-refused',passed=True))
 names=['standalone/check_viewer_file_linked.py','standalone/dos_image.py']
 r=dict(passed=True,binary_sha256=sha(binary),cases=rows,inputs=len(rows),original_inputs=[],sources={**manifest['sources'],**{n:sha(ROOT/n) for n in names}},
  scope=__doc__+' Actual owner, canonical admission/capture reservation and8086 DOS boundary execute; DOS results/errors are modeled, not actual media/SHARE errors. Verify path/call ordering, read-only deny-write/no-inherit AX3DA0, poisoned IO, primary/secondary errors, exactly-once close, retained quarantine/claim, far spans/aliases and ABI. No UI/terminal/physical acceptance.')
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(rows),'linked owner/error/ABI cases')
if __name__=='__main__':main()
