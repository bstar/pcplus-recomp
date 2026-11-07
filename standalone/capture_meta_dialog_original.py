#!/usr/bin/env python3
"""Explicit original Alt-M controller replay over synthetic records and services."""
import argparse,hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP,UC_X86_REG_SI
from pathlib import Path
from check_directory_dial_original import ROOT,Original,DATA,EXPECTED


def records(seed=0,loaded=False):
 out=bytearray()
 for row in range(10):
  text=(('LOAD' if loaded else 'ROW')+str(row)).encode();out+=struct.pack('<H',3 if loaded else (row+seed)%4)+text+b'\0'+bytes([0x5a if loaded else 0xa5])*(51-len(text))
 assert len(out)==540;return bytes(out)


class Dialog(Original):
 def __init__(self,image,overlays,data,keys):
  super().__init__(image,overlays);self.keys=list(keys);self.states=[];self.cursor=0;self.bells=self.loads=self.saves=0;self.field=None
  self.uc.mem_write(DATA+0x3756,data);self.uc.mem_write(DATA+0x21d8,b'LAB.KEY\0');self.put(0x1f7c,0x1f)
  self.put(0x7a6c,1);self.put(0x7a88,6);self.put(0x7a8a,7)
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x13fc7,0x14015,0x14056,0x13226,0x1780e,0x16dca,0x16e5a,0x16e66,0x16e78,0x175e8,0x16bf0,0x17878,0x1376d,0x1e0d0,0x1e16e):return
  sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];cleanup=0;result=0
  if at==0x14056:cleanup=6
  elif at==0x1780e:cleanup=2
  elif at==0x16dca:self.put(0x7a6c,1)
  elif at==0x16e5a:self.put(0x7a6c,0)
  elif at==0x16e66:
   col,row=struct.unpack('<2H',u.mem_read(DATA+sp+2,4));self.cursor=(row<<8)|col;cleanup=4
  elif at==0x16e78:self.cursor=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];cleanup=2
  elif at==0x16bf0:
   source=struct.unpack('<H',u.mem_read(DATA+sp+2,2))[0];self.field=bytes(u.mem_read(DATA+source,50));cleanup=6
  elif at==0x1376d:self.bells+=1
  elif at==0x1e0d0:
   self.loads+=1;u.mem_write(DATA+0x3756,records(loaded=True));u.mem_write(DATA+0x21d8,b'NEXT.KEY\0')
  elif at==0x1e16e:self.saves+=1
  elif at==0x17878:
   assert self.keys,'Unexpected original key request';key=self.keys.pop(0);bp=u.reg_read(UC_X86_REG_BP)
   if ret==0xdfa9:phase=0;row=u.reg_read(UC_X86_REG_SI);kind=self.get(0x3756+row*54)
   elif ret==0xe2ff:phase=1;row=self.get(bp+4);kind=self.get(bp-2)
   else:
    assert ret==0x7abf,hex(ret);phase=2;row_bp=self.get(self.get(bp));row=self.get(row_bp+4);kind=self.get(row_bp-2)
   assert 0<=row<10 and 0<=kind<4
   self.states.append(dict(key=key,phase=phase,row=row,kind=kind,records=bytes(u.mem_read(DATA+0x3756,540)).hex(),bells=self.bells,cursor=self.cursor,shape=(self.get(0x7a88)<<8)|self.get(0x7a8a),field=self.field.hex() if phase==2 else None,name=self.string(0x21d8).decode('ascii'),loads=self.loads,saves=self.saves));result=key
  if at==0x13fc7:u.reg_write(UC_X86_REG_DX,0)
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)


def cases():
 tails=[('kind-cancel',[ord('R'),27,27]),('kind-back',[ord('R'),32,0x0f00,27,27]),
  ('text-cancel',[ord('R'),13,ord('X'),27,27]),('text-accept',[ord('R'),13,ord('X'),13,27]),
  ('text-next',[ord('R'),ord('A'),9,ord('X'),9,27,27]),('text-back-kind-cancel',[ord('R'),ord('A'),13,ord('X'),0x0f00,27,27]),
  ('text-back-row',[ord('R'),ord('A'),13,ord('X'),0x0f00,0x0f00,27,27]),('insert-cancel',[ord('R'),13,0x5200,ord('X'),27,27])]
 for row in range(10):
  for seed in range(4):
   for name,keys in tails:yield f'{name}-{row}-{seed}',records(seed),[9]*row+keys
 for name,keys in [('tab-wrap',[9]*11+[27]),('down-wrap',[0x5000]*11+[27]),('up-wrap',[0x4800]*11+[27]),('back-wrap',[0x0f00]*11+[27]),
  ('unknown',[13,0x1700,27]),('clear-save',[ord('c'),ord('s'),27]),('load-save',[ord('l'),ord('s'),27]),('save-clear-load',[ord('S'),ord('C'),ord('L'),27])]:
  yield name,records(),keys


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED;out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id']==3];vectors=[]
 for name,data,keys in cases():
  o=Dialog(raw,overlays,data,keys);o.call(0xdf44);assert not o.keys and o.uc.reg_read(UC_X86_REG_SP)==0xd002
  vectors.append(dict(name=name,initial=data.hex(),states=o.states,output=bytes(o.uc.mem_read(DATA+0x3756,540)).hex(),bells=o.bells,loads=o.loads,saves=o.saves,final_name=o.string(0x21d8).decode('ascii')))
 tables=sorted({v['initial'] for v in vectors}|{v['output'] for v in vectors}|{s['records'] for v in vectors for s in v['states']});indices={v:i for i,v in enumerate(tables)}
 fields=sorted({s['field'] for v in vectors for s in v['states'] if s['field'] is not None});fi={v:i for i,v in enumerate(fields)}
 for v in vectors:
  v['initial']=indices[v['initial']];v['output']=indices[v['output']]
  v['states']=[[s['key'],s['phase'],s['row'],s['kind'],indices[s['records']],s['bells'],s['cursor'],s['shape'],-1 if s['field'] is None else fi[s['field']],s['name'],s['loads'],s['saves']] for s in v['states']]
 result=dict(passed=True,original_sha256=EXPECTED,format='meta-dialog-traces-v1',tables=tables,fields=fields,state_columns=['key','phase','row','kind','table','bells','cursor','shape','field','name','loads','saves'],
  native_dispatch_evidence='ev_a1a870d1d2c2754325165f8155f2645805d413818b24f53fbf8bf375476f9bbf',
  scope='Actual original df44/e294/7880/79d4/e261/e24a and CRT instructions. Keyboard/window/render/cursor/bell and load/save effects modeled over synthetic records; no real files/VGA/BIOS/UART or physical acceptance.')
 body=json.dumps(result,indent=2);out.write_text(body[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(v,separators=(',',':')) for v in vectors)+'\n  ]\n}\n')
 print('Captured original Meta dialog:',len(vectors),'cases;',sum(len(v['states']) for v in vectors),'key states')


if __name__=='__main__':main()
