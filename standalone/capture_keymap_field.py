#!/usr/bin/env python3
"""Explicit original field CPU oracle. Synthetic fields; modeled UI boundaries."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP
ROOT=Path(__file__).resolve().parents[1]
SHA='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
DATA=0x13f10

def execute(image,initial,keys):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10000,image[512:])
 for reg,value in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x13f1),(UC_X86_REG_SS,0x13f1),(UC_X86_REG_SP,0xf000)):u.reg_write(reg,value)
 u.mem_write(DATA+0xef00,b'\xa5'*256)
 u.mem_write(DATA+0xf000,struct.pack('<5H',0xf000,0x0619,0x0d,0xb000,0xa000))
 u.mem_write(DATA+0xa000,initial+b'\0');u.mem_write(DATA+0xb000,b'\xa5'*40)
 def put(at,v):u.mem_write(DATA+at,struct.pack('<H',v))
 def word(at):return struct.unpack('<H',u.mem_read(DATA+at,2))[0]
 put(0x1554,6);put(0x1556,7);put(0x10cc,6)
 states=[];pending=list(keys);frame=None;cursor=0;bells=0;insert=False
 def hook(cpu,at,size,_):
  nonlocal frame,cursor,bells,insert
  if at==0x1f000:cpu.emu_stop();return
  if at not in (0x1130a,0x112f8,0x11562,0x11580,0x11594,0x110c5,0x10f3c,0x11150):return
  sp=cpu.reg_read(UC_X86_REG_SP);ret=word(sp)
  args=lambda n:struct.unpack('<'+'H'*n,cpu.mem_read(DATA+sp+2,2*n))
  cleanup=0;result=0
  if at==0x1130a:
   source,attribute,position=args(3);assert attribute==13 and position==0x0619
   frame=bytes(cpu.mem_read(DATA+source,10));cleanup=6
  elif at==0x112f8:
   col,row=args(2);assert row==6;cursor=col-25;cleanup=4
  elif at==0x11562:
   attribute,char,position=args(3);assert attribute==13 and position>>8==6
   buf=bytearray(frame);buf[(position&255)-25]=char&255;frame=bytes(buf);cleanup=6
  elif at==0x110c5:put(0x1554,6)
  elif at==0x10f3c:bells+=1
  elif at==0x11150:
   assert frame is not None and pending
   result=pending.pop(0)
   states.append([result,frame.hex(),cursor,word(0x1554),bells])
  cpu.reg_write(UC_X86_REG_AX,result);cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup);cpu.reg_write(UC_X86_REG_IP,ret)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x10a3f,0x20000,count=100000)
 assert not pending and u.reg_read(UC_X86_REG_IP)==0xf000 and u.reg_read(UC_X86_REG_SP)==0xf002
 output=bytes(u.mem_read(DATA+0xb000,40))
 return dict(states=states,result=u.reg_read(UC_X86_REG_AX),output=output.hex(),shape=word(0x1554),bells=bells)

def cases():
 r=[('blank',b'',[13]),('cancel',b'abc',[88,27]),('clear',b'abc',[0x4d00,9,13])]
 for c in range(256):r.append(('byte-'+str(c),b'abc',[c] if c in (13,27) else [c,13]))
 for pos in range(10):
  for name,tail in [('backspace',[0x0e08]),('delete',[0x5300]),('insert',[0x5200,88]),('marker-delete',[0x0e7f]),('marker-rs',[30]),('marker-nul',[0x300]),('ctrl-end',[0x7500]),('left',[0x4b00]),('right',[0x4d00])]:
   r.append((name+'-'+str(pos),b'ABCDEFGHIJ',[0x4700]+[0x4d00]*pos+tail+[13]))
 for n in range(11):r.append(('end-'+str(n),b'A'*n,[0x4f00,27]))
 for name,keys in [('fill',[65]*12+[13]),('insert-markers',[0x5200,30,0x300,0x0e7f,13]),('switch',[0x5200,88,0x5200,89,13])]:r.append((name,b'123456789',keys))
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==SHA
 rows=[]
 for name,initial,keys in cases():
  rows.append(dict(name=name,initial=initial.hex(),**execute(image,initial,keys)))
 result=dict(passed=True,original_sha256=SHA,format='keymap-field-traces-v1',REA_evidence='ev_a35116e66594cd4c22a998dbb2a32aaadb70a413ac8ab4f5c0f928f29d8d7b25',ranges=[dict(start='0xa3f',end_exclusive='0xd4c',sha256=hashlib.sha256(image[512+0xa3f:512+0xd4c]).hexdigest())],cases=rows,limitations=['Actual field and CRT instructions; key, drawing, cursor shape and bell services are models.','Original out-of-field writes on three-byte insert are not adopted; only visible field traced.','No original startup, actual VGA, private files or physical machine tested.'])
 assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True);rows=result.pop('cases');a.output.write_text(json.dumps(result,indent=2)[:-2]+',\n  \"cases\": [\n'+',\n'.join('    '+json.dumps(row,separators=(',',':')) for row in rows)+'\n  ]\n}\n');print('Captured',len(rows),'cases',sum(len(r['states']) for r in rows),'key states')
if __name__=='__main__':main()
