#!/usr/bin/env python3
"""Explicit original eight-cell KEY filename editor replay, synthetic services."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP
from check_directory_dial_original import ROOT,Original,DATA,EXPECTED
class Name(Original):
 def __init__(self,image,overlays,keys):
  super().__init__(image,overlays);self.keys=list(keys);self.states=[];self.bells=0;self.cursor=0;self.field=None
  self.uc.mem_write(DATA+0x5000,b'UNCHANGED\0'+b'\xa5'*54);self.put(0x7a6c,1);self.put(0x7a88,6);self.put(0x7a8a,7)
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x16bf0,0x16e78,0x16dca,0x16e5a,0x17878,0x1376d):return
  sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];cleanup=result=0
  if at==0x16bf0:
   source,attribute,position=struct.unpack('<3H',u.mem_read(DATA+sp+2,6));assert (attribute,position)==(13,0x0911);self.field=bytes(u.mem_read(DATA+source,8));cleanup=6
  elif at==0x16e78:self.cursor=(self.get(sp+2)&255)-17;cleanup=2
  elif at==0x16dca:self.put(0x7a6c,1)
  elif at==0x16e5a:self.put(0x7a6c,0)
  elif at==0x1376d:self.bells+=1
  else:
   assert self.keys and self.field is not None;result=self.keys.pop(0);self.states.append([result,self.field.hex(),self.cursor,(self.get(0x7a88)<<8)|self.get(0x7a8a),self.bells])
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
def cases():
 yield 'empty-enter',[13]
 yield 'escape',[27]
 yield 'typed-enter',list(b'newfile')+[13]
 yield 'typed-tab',list(b'newfile')+[9,13]
 yield 'shift-tab',[0x0f00,13]
 for key in range(256):yield f'byte-{key}',[key] if key in (13,27) else [key,13]
 for pos in range(8):
  for name,tail in [('bs',[8]),('delete',[0x5300]),('insert',[0x5200,ord('!')]),('clear',[0x2e00,ord('!')]),('end',[0x4f00,ord('!')]),('truncate',[0x7500])]:yield f'{name}-{pos}',list(b'ABCDEFGH')+[0x4700]+[0x4d00]*pos+tail+[13]
 for name,tail in [('extra',[ord('X')]),('backspace',[8,ord('X')]),('insert',[0x5200,ord('X')]),('tab',[9,13]),('left',[0x4b00,ord('!')])]:yield f'full-{name}',list(b'ABCDEFGH')+tail+[13] if name!='tab' else list(b'ABCDEFGH')+tail

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id']==3];vectors=[]
 for name,keys in cases():
  o=Name(raw,overlays,keys);o.call(0x7880,[0x4aa7,8,0,0x5000,13,0x0911]);assert not o.keys,(name,o.keys,o.uc.reg_read(UC_X86_REG_AX));vectors.append(dict(name=name,states=o.states,output=bytes(o.uc.mem_read(DATA+0x5000,64)).hex(),result=o.uc.reg_read(UC_X86_REG_AX),bells=o.bells,shape=(o.get(0x7a88)<<8)|o.get(0x7a8a)))
 out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 result=dict(passed=True,format='meta-filename-traces-v1',original_sha256=EXPECTED,REA_callback='ev_6d9e4b765bd0be63bbc2a427f1f3e876ec2414074b9d4144f0ae8c57e68bd2a9',REA_load='ev_01ef5e1485264783ea6b307d6d2fe014634648cec868abf0e81d369775c0bf71',REA_save='ev_8fd8e445cd7d6aec7df9937d24c275c7d372224b3c7f9882aadd233856636611',cases=vectors,scope='Actual original 7880/79d4 and 4aa7 instructions; synthetic empty-source64-byte destination; modeled keyboard/render/cursor/bell. No picker, files, BIOS, UART, VGA or physical acceptance.')
 fields=sorted({state[1] for v in vectors for state in v['states']});indices={field:i for i,field in enumerate(fields)}
 for v in vectors:
  for state in v['states']:state[1]=indices[state[1]]
 result['fields']=fields;result['state_columns']=['key','field_index','cursor','shape','bells'];result.pop('cases');body=json.dumps(result,indent=2)
 out.write_text(body[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(v,separators=(',',':')) for v in vectors)+'\n  ]\n}\n');print('Captured filename field:',len(vectors),'cases,',sum(len(v['states']) for v in vectors),'states')
if __name__=='__main__':main()
