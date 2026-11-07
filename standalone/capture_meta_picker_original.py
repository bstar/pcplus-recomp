#!/usr/bin/env python3
"""Explicit original picker/scroll/sort instructions with synthetic enumeration."""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
from check_directory_dial_original import ROOT,Original,DATA,EXPECTED
class Picker(Original):
 def __init__(self,raw,overlays,names,keys):
  super().__init__(raw,overlays);self.names=names;self.keys=list(keys);self.states=[];self.bells=0;self.firsts=0;self.index=0;self.sorted=None
 def hook(self,u,at,size,_):
  if at==self.stop:u.emu_stop();return
  if at not in (0x182b6,0x15b54,0x15b68,0x1353d,0x13fc7,0x14015,0x175e8,0x16edc,0x16ec2,0x13226,0x17878,0x1376d,0x1427f):return
  sp=u.reg_read(UC_X86_REG_SP);ret=self.get(sp);args=[self.get(sp+i*2) for i in range(1,6)];result=cleanup=0
  if at==0x182b6:
   dest,fmt=args[:2]
   text=(self.string(args[2],9)+b'.KEY') if ret==0xd2ca else b'*.KEY'
   u.mem_write(DATA+dest,text+b'\0')
  elif at in (0x15b54,0x15b68):
   if at==0x15b54:self.firsts+=1;self.index=0
   else:self.index+=1
   result=int(self.index<len(self.names))
   if result:u.mem_write(DATA+0xce3e,self.names[self.index].encode('latin1')+b'.KEY\0')
  elif at==0x1353d:result=0xce6a
  elif at==0x13fc7:u.reg_write(UC_X86_REG_DX,0)
  elif at==0x16edc or at==0x16ec2:cleanup=8
  elif at==0x13226:pass
  elif at==0x17878:
   assert self.keys,'Unexpected native picker key'
   if self.sorted is None:self.sorted=[self.string(0xc062+i*9,9).decode('latin1') for i in range(1,self.get(0x8f94)+1)]
   result=self.keys.pop(0);self.states.append([result,self.get(0x8f98)-1,self.get(0x8f96)-1,self.bells])
  elif at==0x1376d:self.bells+=1
  u.reg_write(UC_X86_REG_AX,result);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
 def run(self):
  self.stop=0x1f000;self.uc.reg_write(UC_X86_REG_SP,0xf000);self.uc.reg_write(UC_X86_REG_BP,0xee00);self.uc.mem_write(DATA+0xf000,struct.pack('<2H',0xf000,0x5000));self.uc.emu_start(0x1d0d0,0x20000,count=30000000);assert self.uc.reg_read(UC_X86_REG_IP)==0xf000 and not self.keys

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raw=a.original.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 overlays=[v for v in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if v['id'] in (1,3)];rng=random.Random(201);cases=[]
 enumerations=[[f'K{i:04}' for i in range(n)] for n in (1,2,14,15,16,29,30,31,100,350)]
 enumerations.append(['a','B','A2','a1','!FIRST','_LAST','ZZZZZZZZ','mIxEd','K000001','@LOC','0','9','X-Y','P!Q','Z','C','\x80LOC','\xffLOC'])
 for names in enumerations:
  count=len(names);rng.shuffle(names)
  sequences=[[13],[27],[0x4f00,13],[0x5000]*18+[0x4800]*18+[13],[0x5100]*25+[0x4900]*25+[13],[0x4f00,0x4800,0x4700,0x5000,0x4900,13]]
  sequences += [[rng.choice([0x4700,0x4800,0x4900,0x4f00,0x5000,0x5100,65,9]) for _ in range(40)]+[13] for _ in range(3)]
  for keys in sequences:
   o=Picker(raw,overlays,names,keys)
   try:o.run()
   except Exception:
    print('Native picker failure',count,keys,'IP',hex(o.uc.reg_read(UC_X86_REG_IP)),'SP',hex(o.uc.reg_read(UC_X86_REG_SP)),'states',o.states[-3:]);raise
   cases.append(dict(names=names,sorted=o.sorted,states=o.states,result=o.uc.reg_read(UC_X86_REG_AX),selected=o.string(0xce6a,13).decode('latin1'),bells=o.bells))
 out=a.output.resolve();assert out.is_relative_to(ROOT) and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 result=dict(passed=True,format='meta-picker-traces-v1',original_sha256=EXPECTED,cases=cases,scope='Actual original d0d0/d304/d38a/d3e9/d446 and CRT sort/string instructions; enumeration, formatting and UI/keyboard/bell services modeled over unique synthetic stems. Counts1..350; no DOS/BIOS/UART/VGA/physical acceptance. Stack moved beyond list storage in analyst replay.')
 tables=[]
 def table(names):
  if names not in tables:tables.append(names)
  return tables.index(names)
 for case in cases:case['names']=table(case['names']);case['sorted']=table(case['sorted'])
 result['tables']=tables;result.pop('cases');body=json.dumps(result,indent=2)
 out.write_text(body[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(v,separators=(',',':')) for v in cases)+'\n  ]\n}\n');print('Captured picker:',len(cases),'cases;',sum(len(c['states']) for c in cases),'states')
if __name__=='__main__':main()
