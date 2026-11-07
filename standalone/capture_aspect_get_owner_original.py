#!/usr/bin/env python3
"""Explicit original GET owner replay: real readers, field and integer CRT."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP
from capture_aspect_get_field_original import Field
from check_directory_dial_original import ROOT,DATA,EXPECTED

class Owner(Field):
 def __init__(self,raw,overlays,case):
  super().__init__(raw,overlays,80,b'',case['keys'],1,0x0607)
  self.case=case;self.events=[];self.position=case['row']*256+case['column'];self.failure=None;self.field_calls=0
  token=case['token'];kind=token%10
  if token<150:tail=b'\0'
  else:tail=struct.pack('<H',24)
  width=case['width'];self.stream=bytes([token])+tail+(b'\0' if width is None else b'\1\xab'+struct.pack('<H',width&65535));self.put(0x4b02,0x7000);self.put(0x7000,0x7100);self.put(0x7002,len(self.stream));self.uc.mem_write(DATA+0x7100,self.stream)
  self.put(0xe13a,0xb000);self.put(0x4b06,0x6000);self.put(0xe37c,1);self.put(0xe380,case['keys_disabled'])
  self.put(0x399c,case['row']);self.put(0x399e,case['column']);self.put(0x1f70,13);self.put(0x1d46,case['wrap']);self.put(0x7a80,25);self.put(0x7a72,80);self.put(0xce2e,0)
  self.uc.mem_write(DATA+0x6000,b'123\0'+b'\xa5'*78)
  if token==100:self.destination=DATA+0xd13a
  elif token>=160:self.destination=DATA+0xb018
  elif token>=150:self.destination=DATA+0xafe8
  elif kind==0:
   self.uc.mem_write(DATA+0xdb82,struct.pack('<2H',0x100,0x5000));self.destination=0x50100
  else:self.destination=DATA+{1:0xd482,2:0xd582,3:0xd782}[kind]
  self.size={0:81,1:2,2:4,3:8}[kind]
  self.before=(b'old text\0'+b'\xa5'*72) if kind==0 else bytes.fromhex('785634129abcdef0')[:self.size]
  self.uc.mem_write(self.destination,self.before)
 @property
 def read(self):return self.get(0x7000)-0x7100
 def hook(self,u,at,size,ctx):
  if at==0x179d4:
   sp=u.reg_read(UC_X86_REG_SP);callback,masked,width,initial,output,attribute,position=struct.unpack('<7H',u.mem_read(DATA+sp+2,14))
   self.width=width;self.field_calls+=1
   self.events.append(['field',callback,masked,width,initial!=0,attribute,position]);return
  if at not in (0x14cb4,0x1e129,0x14efb,0x1798e,0x11bbe,0x14e6b,0x14ebc,0x1d408):
   if at in (0x16bf0,0x16e78):
    sp=u.reg_read(UC_X86_REG_SP)
    if at==0x16bf0:
     source,attribute,position=struct.unpack('<3H',u.mem_read(DATA+sp+2,6));self.frame=bytes(u.mem_read(DATA+source,self.width));cleanup=6
    else:
     self.position=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];self.cursor=(self.position&255)-self.case['column'];cleanup=2
    ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret);return
   return super().hook(u,at,size,ctx)
  sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];cleanup=0;result=0
  if at in (0x14cb4,0x1e129):
   count=1 if at==0x14cb4 else 2;assert self.read+count<=len(self.stream),'unexpected stream read'
   result=int.from_bytes(self.stream[self.read:self.read+count],'little');self.put(0x7000,self.get(0x7000)+count);self.put(0x7002,self.get(0x7002)-count)
  elif at==0x14efb:
   self.failure=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];self.events.append(['native-error',self.failure]);u.reg_write(UC_X86_REG_IP,0xf000);u.emu_stop();return
  elif at==0x1798e:result=self.position
  elif at==0x11bbe:self.events.append(['cursor',u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)])
  elif at==0x14e6b:result=self.case['confirm'];self.events.append(['confirm',result])
  elif at==0x14ebc:
   self.events.append(['cancel-dispatch']);u.reg_write(UC_X86_REG_IP,0xf000);u.emu_stop();return
  else:
   selector=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];assert selector==5;cleanup=2
   self.events.append(['float-service',selector,self.string(self.get(0xe142)).hex()])
   u.mem_write(DATA+0xe150,bytes.fromhex('0123456789abcdef'))
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)

def cases():
 for token in (100,140,141,142,143,150,151,152,153,160,161,162,163):
  for name,keys,width,confirm,disabled in [('enter',list(b'-42.5')+[13],10,0,0),('cancel-declined',[ord('7'),27],10,0,0),('cancel-confirmed',[27],10,1,0),('cancel-disabled',[27],10,1,1),('width-zero',[],0,0,0),('width-default',[13],None,0,0),('width80',[13],80,0,0),('width81',[],81,0,0),('width-negative',[],-1,0,0)]:
   yield dict(name=f'{token}-{name}',token=token,keys=keys,width=width,confirm=confirm,keys_disabled=disabled,row=6,column=0,wrap=0)
 for row,column,wrap in [(23,75,0),(24,75,0),(23,75,1),(24,75,1),(24,79,1)]:
  yield dict(name=f'clip-{row}-{column}-{wrap}',token=141,keys=[49,50,13],width=None,confirm=0,keys_disabled=0,row=row,column=column,wrap=wrap)
 for token in (141,142):
  for text in (b'',b'-',b'.5',b'--1',b'1.9',b'32768',b'65536',b'4294967296',b'-2147483649',b'9'*80):
   yield dict(name=f'parse-{token}-{text.decode()}',token=token,keys=list(text)+[13],width=80,confirm=0,keys_disabled=0,row=6,column=0,wrap=0)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id'] in (16,17)];vectors=[]
 for case in cases():
  oracle=Owner(raw,overlays,case);oracle.call(0xf280)
  assert oracle.failure==(1 if case['width'] in (81,-1) else None),(case['name'],oracle.failure)
  assert oracle.read==len(oracle.stream) and not oracle.keys
  returned=not oracle.failure and not any(e[0]=='cancel-dispatch' for e in oracle.events)
  if returned:assert oracle.uc.reg_read(UC_X86_REG_SP)==0xd002
  case.update(before=oracle.before.hex(),output=bytes(oracle.uc.mem_read(oracle.destination,oracle.size)).hex(),comparison=oracle.get(0xd124),events=oracle.events,field_calls=oracle.field_calls,states=oracle.states,bells=oracle.bells,stream_consumed=oracle.read,native_error=oracle.failure,returned=returned);vectors.append(case)
 result=dict(passed=True,format='aspect-get-owner-v1',original_sha256=EXPECTED,cases=vectors,
  scope='Actual original mode0 GET owner, typed readers/global string copy+flush, field/callbacks and integer/long CRT. Synthetic operand stream; modeled keyboard/display/cursor/bell, cancel decision/nonreturn dispatch, and opaque float service5 (NOT float conversion). Native error boundary stopped. No real FILE/BIOS/VGA/UART, complete float runtime or physical acceptance.')
 out.write_text(json.dumps(result,indent=2)+'\n');print('Captured original GET owner:',len(vectors),'cases')

if __name__=='__main__':main()
