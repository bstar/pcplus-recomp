#!/usr/bin/env python3
"""Explicit original GET field/callback replay with synthetic peripheral services."""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_DS,UC_X86_REG_SS
from check_directory_dial_original import ROOT,Original,DATA,EXPECTED

class Field(Original):
 def __init__(self,image,overlays,width,initial,keys,visible,shape):
  super().__init__(image,overlays);self.width=width;self.keys=list(keys);self.states=[];self.bells=0;self.cursor=0;self.frame=None
  self.uc.mem_write(DATA+0x5000,initial+b'\0');self.uc.mem_write(DATA+0x5100,b'\xa5'*82)
  self.put(0x7a6c,visible);self.put(0x7a88,shape>>8);self.put(0x7a8a,shape&255)
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x16bf0,0x16e78,0x16dca,0x16e5a,0x17878,0x1376d):return
  sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];cleanup=0;result=0
  if at==0x16bf0:
   source,attribute,position=struct.unpack('<3H',u.mem_read(DATA+sp+2,6));assert attribute==0x0d and position==0x0600
   self.frame=bytes(u.mem_read(DATA+source,self.width));cleanup=6
  elif at==0x16e78:
   position=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];assert position>>8==6
   self.cursor=position&255;cleanup=2
  elif at==0x16dca:self.put(0x7a6c,1)
  elif at==0x16e5a:self.put(0x7a6c,0)
  elif at==0x1376d:self.bells+=1
  else:
   assert self.frame is not None and self.keys,'Unexpected original key request'
   result=self.keys.pop(0);self.states.append([result,self.frame.hex(),self.cursor,(self.get(0x7a88)<<8)|self.get(0x7a8a),self.get(0x7a6c),self.bells])
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)

def cases():
 rng=random.Random(20149)
 for width in (1,2,10,50,80,81):
  for numeric in (0,1):
   for trial in range(12):
    keys=[rng.choice([0,8,9,32,45,46,48,49,50,65,255,0x0e08,0x0e7f,0x2e00,0x4700,0x4b00,0x4d00,0x4f00,0x5200,0x5300,0x7500]) for _ in range(64)]
    yield dict(name=f'mixed-{width}-{numeric}-{trial}',width=width,numeric=numeric,masked=trial%2,visible=trial%2,shape=0x0607,initial=b'1 '*(width//2),keys=keys+[13 if trial%2 else 27])
 yield dict(name='single-full-space-backspace',width=1,numeric=0,masked=0,visible=1,shape=0x0607,initial=None,keys=[32,8,13])
 for width in (1,2,10,50,80,81):
  for numeric in (0,1):
   for masked in (0,1):
    for visible in (0,1):
     for initial in (None,b'',b'1'*(width-1),b'2'*width):
      for finish in (13,27):
       yield dict(name=f'boundary-{width}-{numeric}-{masked}-{visible}-{None if initial is None else len(initial)}-{finish}',width=width,numeric=numeric,masked=masked,visible=visible,shape=0x0607,initial=initial,keys=[0x4f00,ord('3'),ord('4'),8,finish])
 for numeric in (0,1):
  for key in range(256):
   yield dict(name=f'byte-{numeric}-{key}',width=10,numeric=numeric,masked=0,visible=1,shape=0x0607,initial=b'12 34',keys=[key] if key in (13,27) else [key,13])
  for width in (1,2,10,50,80,81):
   for at in sorted({0,width//2,width-1}):
    for key in (8,0x0e08,0x0e7f,0x2e00,0x4700,0x4b00,0x4d00,0x4f00,0x5200,0x5300,0x7500,0x0f00,0x4be0):
     yield dict(name=f'edit-{numeric}-{width}-{at}-{key}',width=width,numeric=numeric,masked=1,visible=0,shape=0x0a0f,initial=b'1'*width,keys=[0x4d00]*at+[key,ord('2'),13])
   for key in (8,0x0e08,0x5300,0x5200,0x4f00,0x4700,0x7500,0x4d00):
    yield dict(name=f'full-{numeric}-{width}-{key}',width=width,numeric=numeric,masked=0,visible=1,shape=0x0607,initial=None,keys=[ord('1')]*width+[key,ord('2'),13])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id']==17];vectors=[]
 for case in cases():
  oracle=Field(raw,overlays,case['width'],case['initial'] or b'',case['keys'],case['visible'],case['shape'])
  oracle.call(0x79d4,[0xf479 if case['numeric'] else 0x3f9c,case['masked'],case['width'],0 if case['initial'] is None else 0x5000,0x5100,0x0d,0x0600])
  assert not oracle.keys and len(oracle.states)==len(case['keys'])
  assert oracle.uc.reg_read(UC_X86_REG_SP)==0xd010 and oracle.uc.reg_read(UC_X86_REG_DS)==oracle.uc.reg_read(UC_X86_REG_SS)==DATA>>4
  assert oracle.string(0x5000)==(case['initial'] or b'')
  case.pop('keys');case['initial']=None if case['initial'] is None else case['initial'].hex()
  case.update(states=oracle.states,output=bytes(oracle.uc.mem_read(DATA+0x5100,82)).hex(),result=oracle.uc.reg_read(UC_X86_REG_AX),bells=oracle.bells,final_shape=(oracle.get(0x7a88)<<8)|oracle.get(0x7a8a),final_visible=oracle.get(0x7a6c));vectors.append(case)
 fields=sorted({s[1] for v in vectors for s in v['states']});indices={s:i for i,s in enumerate(fields)}
 for v in vectors:
  for s in v['states']:s[1]=indices[s[1]]
 ranges=[]
 for start,end,offset in [(0x79d4,0x7d12,0x1200+0x79d4),(0x3f9c,0x3fb0,0x1200+0x3f9c),(0xf479,0xf4b6,117808+0xf479-0xf280)]:
  ranges.append(dict(start=start,end_exclusive=end,source_file_offset=offset,sha256=hashlib.sha256(raw[offset:offset+end-start]).hexdigest()))
 result=dict(passed=True,format='aspect-get-field-v1',original_sha256=EXPECTED,native_ranges=ranges,REA_field='ev_431892296f1a449f84b3ca459253ec00d76f549853cc34941ca685b228e8a5eb',fields=fields,state_columns=['key','field_index','cursor','shape','visible','bells'],cases=vectors,
  scope='Actual original79D4/3F9C/F479 and original CRT instructions; synthetic separate initial/output buffers, widths1..81, masked/unmasked and numeric/string callbacks. Keyboard/display/cursor/visibility/bell services modeled. No BIOS/VGA/UART, conversions, GET owner, runtime or physical acceptance.')
 rows=result.pop('cases');out.write_text(json.dumps(result,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(v,separators=(',',':')) for v in rows)+'\n  ]\n}\n')
 print('Captured original GET field:',len(vectors),'cases,',sum(len(v['states']) for v in vectors),'key states')

if __name__=='__main__':main()
