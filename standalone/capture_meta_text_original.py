#!/usr/bin/env python3
"""Explicit original-instruction field replay; synthetic text and UI services."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_DS,UC_X86_REG_SS
from check_directory_dial_original import ROOT,Original,DATA,EXPECTED


class Field(Original):
 def __init__(self,image,overlays,initial,keys):
  super().__init__(image,overlays);self.keys=list(keys);self.states=[];self.bells=0;self.cursor=0;self.frame=None
  self.uc.mem_write(DATA+0x5000,initial);self.put(0x7a6c,1);self.put(0x7a88,6);self.put(0x7a8a,7)
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x16bf0,0x16e78,0x16dca,0x16e5a,0x17878,0x1376d):return
  sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];cleanup=0;result=0
  if at==0x16bf0:
   source,attribute,position=struct.unpack('<3H',u.mem_read(DATA+sp+2,6));assert attribute==0x0d and position==0x0619
   self.frame=bytes(u.mem_read(DATA+source,50));cleanup=6
  elif at==0x16e78:
   position=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];assert position>>8==6
   self.cursor=(position&255)-25;cleanup=2
  elif at==0x16dca:self.put(0x7a6c,1)
  elif at==0x16e5a:self.put(0x7a6c,0)
  elif at==0x1376d:self.bells+=1
  else:
   assert self.frame is not None and self.keys,'Unexpected original key request'
   result=self.keys.pop(0);self.states.append(dict(key=result,field=self.frame.hex(),cursor=self.cursor,shape=(self.get(0x7a88)<<8)|self.get(0x7a8a),bells=self.bells))
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)


def cases():
 base=(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'*2)[:50]
 result=[('blank-enter',b'',[13]),('blank-escape',b'',[27]),('overwrite-cancel',b'unchanged',[ord('X'),27]),
  ('tab-accept',b'abc',[ord('X'),9]),('shift-tab-accept',b'abc',[ord('X'),0x0f00]),
  ('callback-reject-ff',b'abc',[255,13]),('raw-control-and-del',b'',[1,31,127,254,13]),
  ('nul-refused',b'abc',[0,13]),('leading-trailing-spaces',b' a b   ',[13]),
  ('alt-c-resets-cursor',b'abc',[0x4d00,0x2e00,ord('!'),13]),
  ('extended-clear',b'abc',[0x4d00,0x0e7f,ord('!'),13]),
  ('literal-e0-scan',b'abc',[0x4be0,13])]
 for length in (0,1,49,50,51):
  for end in (13,27,9,0x0f00):result.append((f'initial-{length}-finish-{end}',b'A'*length,[0x4f00,ord('!'),end]))
 for key in range(256):result.append((f'byte-key-{key}',b'abc',[key] if key in (9,13,27) else [key,13]))
 for at in range(50):
  prefix=[0x4700]+[0x4d00]*at
  for name,tail in [('backspace',[8]),('delete',[0x5300]),('insert',[0x5200,ord('!')]),('ctrl-end',[0x7500]),('left',[0x4b00,ord('!')])]:
   result.append((f'{name}-{at}',base,prefix+tail+[13]))
 fill=list(b'A'*50)
 for name,tail in [('extra',[ord('X')]),('backspace',[8,ord('X')]),('extended-backspace',[0x0e08,ord('X')]),
  ('delete',[0x5300,ord('X')]),('insert',[0x5200,ord('X')]),('end',[0x4f00,ord('X')]),('home',[0x4700,ord('X')]),('ctrl-end',[0x7500,ord('X')])]:
  for finish in (13,27):result.append(('full-'+name+'-'+str(finish),b'',fill+tail+[finish]))
 return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id']==3];vectors=[]
 for name,text,keys in cases():
  initial=text+b'\0'+b'\xa5'*(51-len(text));assert len(initial)==52
  oracle=Field(raw,overlays,initial,keys);oracle.call(0x7880,[0xe261,50,0x5000,0x5000,0x0d,0x0619])
  assert not oracle.keys and len(oracle.states)==len(keys)
  assert oracle.uc.reg_read(UC_X86_REG_SP)==0xd00e and oracle.uc.reg_read(UC_X86_REG_DS)==oracle.uc.reg_read(UC_X86_REG_SS)==DATA>>4
  vectors.append(dict(name=name,initial=initial.hex(),states=oracle.states,output=bytes(oracle.uc.mem_read(DATA+0x5000,52)).hex(),result=oracle.uc.reg_read(UC_X86_REG_AX),bells=oracle.bells,shape=(oracle.get(0x7a88)<<8)|oracle.get(0x7a8a)))
 ranges=[dict(start=0x7880,end_exclusive=0x789f),dict(start=0x79d4,end_exclusive=0x7d12)]
 for r in ranges:
  r['source_file_offset']=0x1200+r['start'];r['sha256']=hashlib.sha256(raw[0x1200+r['start']:0x1200+r['end_exclusive']]).hexdigest()
 fields=sorted({s['field'] for v in vectors for s in v['states']});indices={s:i for i,s in enumerate(fields)}
 for v in vectors:v['states']=[[s['key'],indices[s['field']],s['cursor'],s['shape'],s['bells']] for s in v['states']]
 result=dict(passed=True,format='meta-field-traces-v1',state_columns=['key','field_index','cursor','shape','bells'],fields=fields,original_sha256=EXPECTED,native_ranges=ranges,REA_pseudocode='ev_8c003c884636ef6c380b8805a8406868f097d76ba0b450d3bfe38dbd8cf4a278',cases=vectors,
  scope='Actual original 7880/79d4 and overlay3 e261 callback instructions plus original CRT helpers. Synthetic52-byte strings only; keyboard, display, cursor, visibility and bell boundaries modeled. No DOS/BIOS/UART, actual screen pixels, file persistence or physical acceptance.')
 # Repeated frame cells are pooled; each authored case stays one reviewable row.
 rows=result.pop('cases');body=json.dumps(result,indent=2)
 out.write_text(body[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(v,separators=(',',':')) for v in rows)+'\n  ]\n}\n')
 print('Captured original Meta text:',len(vectors),'cases,',sum(len(v['states']) for v in vectors),'key states')


if __name__=='__main__':main()
