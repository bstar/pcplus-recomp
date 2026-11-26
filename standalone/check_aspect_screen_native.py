#!/usr/bin/env python3
"""Native screen handlers/coordinate readers with explicit operand/platform peers."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
CODE,DATA,VIDEO,STACK,STOP=0x10000,0x40000,0xb8000,0x9000,0x100
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
FIELDS=[('box',17,0xe6d1,47),('clear',17,0xe700,19),('locate',17,0xe7e5,37),
        ('scroll',17,0xe847,27),('getvattr',18,0xea23,13),('putvattr',18,0xea3c,17),
        ('physical_offset',18,0xeadc,19),('row',16,0xddcd,11),('column',16,0xddd8,11),('position',16,0xde27,19)]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def signed(v):return v if v<32768 else v-65536


class Machine:
 def __init__(self,binaries,native_frame=False):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  for start,code in binaries.items():self.u.mem_write(CODE+start,code)
  self.events=[];self.operands=[];self.options=[];self.aborted=False;self.snow=[];self.native_frame=native_frame
  # Checked native integer/optional/destination readers consume these boundaries.
  peers={0xdc48:self.integer,0x4cb4:self.option,0xde4d:self.destination,0x4efb:self.error,
         0x6edc:self.scroll,0x4056:self.box,0x1bbe:self.cursor,0x2530:self.erase,
         0x7f62:self.cell,0x79a8:self.horizontal,0x7f4a:self.vertical,0x2adc:self.adjust}
  for at,callback in peers.items():
   if native_frame and at in (0x7f62,0x79a8,0x7f4a):continue
   self.u.hook_add(UC_HOOK_CODE,lambda u,a,s,x,fn=callback:fn(),begin=CODE+at,end=CODE+at)
  self.u.hook_add(UC_HOOK_CODE,lambda u,a,s,x:self.events.append(('reset',)),begin=CODE+0x24da,end=CODE+0x24da)
  self.u.hook_add(UC_HOOK_INSN,self.port_in,None,1,0,UC_X86_INS_IN)
 def word(self,at,value=None):
  if value is not None:self.u.mem_write(DATA+at,struct.pack('<H',value&65535))
  return struct.unpack('<H',self.u.mem_read(DATA+at,2))[0]
 def ax(self,v):self.u.reg_write(UC_X86_REG_AX,v&65535)
 def args(self,n):return struct.unpack('<'+'H'*n,self.u.mem_read(DATA+self.u.reg_read(UC_X86_REG_SP)+2,n*2))
 def ret(self,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);ip=self.word(sp)
  self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup);self.u.reg_write(UC_X86_REG_IP,ip)
 def integer(self):
  assert self.operands,'unexpected integer read';v=self.operands.pop(0);self.events.append(('integer',v));self.ax(v);self.ret()
 def option(self):
  assert self.options,'unexpected byte read';v=self.options.pop(0);self.events.append(('option',v));self.ax(v);self.ret()
 def destination(self):self.events.append(('destination',));self.ax(0x6102);self.ret()
 def error(self):
  self.events.append(('error',*self.args(1)))
  if self.abort_on_error:self.aborted=True;self.u.emu_stop()
  else:self.ret(2)
 def scroll(self):self.events.append(('scroll',*self.args(4)));self.ret(8)
 def box(self):self.events.append(('box',*self.args(3)));self.ret(6)
 def cursor(self):self.events.append(('cursor',self.u.reg_read(UC_X86_REG_AX),self.u.reg_read(UC_X86_REG_DX)));self.ret()
 def erase(self):self.events.append(('erase',*self.args(4)));self.ret(8)
 def cell(self):self.events.append(('cell',*self.args(2)));self.ret(4)
 def horizontal(self):self.events.append(('horizontal',*self.args(3)));self.ret(6)
 def vertical(self):self.events.append(('vertical',*self.args(3)));self.ret(6)
 def adjust(self):self.events.append(('adjust',*self.args(2)));self.ret(4)
 def port_in(self,u,port,size,x):
  assert port==0x3da and size==1 and self.snow
  return self.snow.pop(0)
 def run(self,start,operands=(),options=(),setup=None,args=(),abort=False,exit_state=0,check_range=1):
  self.events=[];self.operands=list(operands);self.options=list(options);self.aborted=False;self.abort_on_error=abort
  u=self.u
  for r,v in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4),
              (UC_X86_REG_ES,0x1234),(UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369c)]:u.reg_write(r,v)
  u.reg_write(UC_X86_REG_EFLAGS,2);u.reg_write(UC_X86_REG_SP,STACK)
  frame=struct.pack('<'+'H'*(len(args)+1),STOP,*args);u.mem_write(DATA+STACK,frame+b'AFTER')
  for at,v in {0x7a74:25,0x7a80:24,0x7a7e:79,0x7a7a:160,0x7a78:0xb800,0x7a8e:0,
               0x7a72:80,0x1d2e:0,0x1d32:0x1234,0x1f70:0x5678,0x334a:23,0x3258:79,0xceb0:2,
               0xe37c:check_range,0xe378:exit_state,0x3734:0,0x6100:0x1357,0x6102:0xa5a5,0x6104:0x2468}.items():self.word(at,v)
  for at,v in (setup or {}).items():self.word(at,v)
  before_data=bytes(u.mem_read(DATA,65536)) if self.native_frame else None
  u.emu_start(CODE+start,CODE+STOP,count=3000000 if self.native_frame else 3000)
  if not self.aborted:
   assert u.reg_read(UC_X86_REG_IP)==STOP,(hex(start),self.events)
   assert u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
   assert not self.operands and not self.options,(hex(start),self.events,self.operands,self.options)
   assert u.reg_read(UC_X86_REG_BP)==0x1357 and u.reg_read(UC_X86_REG_SI)==0x2468 and u.reg_read(UC_X86_REG_DI)==0x369c
   assert bytes(u.mem_read(DATA+STACK,len(frame)+5))==frame+b'AFTER'
  assert u.reg_read(UC_X86_REG_DS)==DATA>>4 and u.reg_read(UC_X86_REG_SS)==DATA>>4
  assert self.word(0x6100)==0x1357 and self.word(0x6104)==0x2468
  if before_data is not None:
   after_data=bytes(u.mem_read(DATA,65536));end=STACK+len(frame)+5
   assert after_data[:STACK-256]==before_data[:STACK-256] and after_data[end:]==before_data[end:]
  return u.reg_read(UC_X86_REG_AX),self.events


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 provenance=json.loads((ROOT/'reconstruction/aspect_screen_commands/provenance.json').read_text())
 sources=['src/aspect/screen_commands.asm','standalone/check_aspect_screen_native.py','reconstruction/aspect_screen_commands/provenance.json','reconstruction/uart/encodings.inc']
 original=a.original.read_bytes() if a.original else None
 if original is not None:
  assert hashlib.sha256(original).hexdigest()==ORIGINAL
  frame=provenance['original_default_frame']
  assert struct.unpack_from('<H',original,0x28ca2)[0]==0x1b7a
  assert original[0x274ca:0x274d2]==bytes.fromhex(frame['glyph_hex'])==bytes.fromhex('c9 cd bb ba bc cd c8 ba')
 overlays=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if original is not None else []
 binaries={};units=[]
 def assemble(name,source,defines,start):
  source_path=ROOT/source;sources.append(source);path=out/(name+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',*['-D'+d for d in defines],str(source_path),'-o',str(path)],check=True)
  binaries[start]=path.read_bytes();return path
 for unit,(name,overlay,start,size) in enumerate(FIELDS,1):
  path=assemble(name,'src/aspect/screen_commands.asm',['ASPECT_SCREEN_FLAT','ASPECT_SCREEN_UNIT='+str(unit)],start)
  assert len(binaries[start])==size and sha(path)==provenance['units'][unit-1]['binary_sha256']
  if original is not None:
   o=next(o for o in overlays if o['id']==overlay);base=o['source_file_offset']-16*o['relative_load_segment'];assert binaries[start]==original[base+start:base+start+size]
  units.append(dict(name=name,entry=hex(start),bytes=size,sha256=sha(path)))
 helpers=[('bounded','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=2'],0xdd68),
          ('optional','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=4'],0xe0e4),
          ('byte','src/aspect/string_services.asm',['ASPECT_STRING_SERVICES_FLAT','ASPECT_STRING_SERVICES_UNIT=4'],0xdde3),
          ('store','src/aspect/string_services.asm',['ASPECT_STRING_SERVICES_FLAT','ASPECT_STRING_SERVICES_UNIT=6'],0xde3a),
          ('clearhome','reconstruction/terminal_services/clear_home.asm',[],0x24e2),
          ('reset','reconstruction/attributes/reset.asm',[],0x24da),
          ('home','reconstruction/input_dispatch/home.asm',[],0x1f56),
          ('read','reconstruction/ui_windows/read_byte.asm',[],0x6fa0),
          ('write','reconstruction/notice_window/attribute.asm',[],0x6c84),
          ('frame','reconstruction/notice_window/frame.asm',[],0x6fec),
          ('horizontal','reconstruction/notice_window/horizontal.asm',[],0x79a8),
          ('vertical','reconstruction/notice_window/vertical.asm',[],0x7f4a),
          ('cell','reconstruction/notice_window/cell.asm',[],0x7f62),
          ('fill','reconstruction/program_ui/fill.asm',[],0x6c20),
          ('stride','reconstruction/notice_window/stride.asm',[],0x8034),
          ('writecell','reconstruction/notice_window/write.asm',[],0x6cb4),
          ('offset8','reconstruction/program_ui/cell_offset.asm',[],0x7e02)]
 reused=[]
 for name,source,defines,start in helpers:
  path=assemble(name,source,defines,start)
  if original is not None:
   if start>=0xd000:
    o=next(o for o in overlays if o['id']==16);base=o['source_file_offset']-16*o['relative_load_segment']
   else:base=0x1200
   assert binaries[start]==original[base+start:base+start+len(binaries[start])],name
  reused.append(dict(name=name,entry=hex(start),bytes=len(binaries[start]),sha256=sha(path)))
 # Both OMF placements must assemble without changing recovered flat bodies.
 for far in (False,True):subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*(['-DASPECT_SCREEN_FAR'] if far else []),str(ROOT/'src/aspect/screen_commands.asm'),'-o',str(out/('bank.obj' if far else 'near.obj'))],check=True)
 identities={n:sha(ROOT/n) for n in sorted(set(sources))}
 m=Machine(binaries);cases=0
 def run(*args,**kwargs):
  nonlocal cases;cases+=1;return m.run(*args,**kwargs)
 # Independent literal platform contracts, distinctive corners/attribute values.
 for attr in range(256):
  _,events=run(0xe6d1,[2,3,7,11,attr]);assert events==[('integer',2),('integer',3),('integer',7),('integer',11),('integer',attr),('scroll',attr,0x070b,0x0203,0),('box',attr,0x070b,0x0203)]
  _,events=run(0xe847,[5,2,3,7,11,attr]);assert events[-1]==('scroll',attr,0x070b,0x0203,5)
  _,events=run(0xe700,[attr],[1]);assert events==[('option',1),('integer',attr),('reset',),('erase',attr,0x174f,0,0),('reset',),('cursor',2,0)]
  assert m.word(0x1d32)==m.word(0x1f70)==attr
 for option in (0,2,255,65535):
  _,events=run(0xe700,options=[option]);assert events==[('option',option),('erase',0x1234,0x174f,0,0),('reset',),('cursor',2,0)]
  assert m.word(0x1d32)==m.word(0x1f70)==0x1234
 for wide in (0,1,0x8000,65535):
  for col in (0,79,80,131,132,65535):
   _,events=run(0xe7e5,[24,col],setup={0x1d2e:wide},abort=True)
   if col>(131 if wide else 79):assert m.aborted and events[-1]==('error',1)
   else:assert events[-1]==('cursor',24,col)
 for count in (0,25):
  _,events=run(0xe847,[count,0,0,24,79,255]);assert events[-1]==('scroll',255,0x184f,0,count)
 # Refusal must occur at the actual bound reader before any platform mutation.
 refused=[(0xe6d1,[25,0,24,79,7]),(0xe6d1,[0,80,24,79,7]),
          (0xe6d1,[0,0,24,79,256]),(0xe700,[256]),
          (0xe847,[26,0,0,24,79,7]),(0xe847,[65535,0,0,24,79,7]),
          (0xea23,[25,0]),(0xea23,[0,80]),(0xea3c,[0,0,256])]
 for start,values in refused:
  _,events=run(start,values,options=[1] if start==0xe700 else [],abort=True)
  assert m.aborted and events[-1]==('error',1)
  assert all(e[0] in ('integer','option','error') for e in events)
  assert m.word(0x1d32)==0x1234 and m.word(0x1f70)==0x5678 and m.word(0x6102)==0xa5a5
 # Exhaust raw WORD coordinates using the real shared signed range checker.
 for start,limit in ((0xddcd,24),(0xddd8,79)):
  for value in range(65536):
   result,events=run(start,[value],exit_state=1)
   valid=0<=signed(value)<=limit
   assert result==(value if valid else 0)
   assert events==[('integer',value)]+([] if valid else [('error',1)])
 for values in ((0,0),(24,79),(7,39),(0xffff,0x1234),(0x1234,0x5678)):
  row,col=values;result,_=run(0xde27,values,check_range=0)
  assert result==((col|((row&255)<<8))&65535)
  result,_=run(0xeadc,values,check_range=0,setup={0x7a7a:0xfff1})
  assert result==(row*0xfff1+2*col)&65535
 # Physical last/status row is admitted; attribute reads/writes retain character.
 for row,col in ((0,0),(24,79),(12,40)):
  offset=row*160+2*col+1
  for attr in range(256):
   image=bytes([0xa5])*4002;m.u.mem_write(VIDEO,image)
   _,events=run(0xea3c,[row,col,attr]);changed=bytearray(image);changed[offset]=attr
   assert bytes(m.u.mem_read(VIDEO,len(image)))==changed
   assert m.word(0x1d32)==0x1234 and m.word(0x1f70)==0x5678
   result,events=run(0xea23,[row,col]);assert m.word(0x6102)==attr and events[-1]==('destination',)
 # Actual video primitives' controlled CGA path enables IF; normal path retains it.
 m.snow=[0,1];run(0xea3c,[24,79,0x7f],setup={0x7a8e:0x3da});assert not m.snow and m.u.reg_read(UC_X86_REG_EFLAGS)&0x200
 m.snow=[0,1];run(0xea23,[24,79],setup={0x7a8e:0x3da});assert not m.snow and m.word(0x6102)==0x7f and m.u.reg_read(UC_X86_REG_EFLAGS)&0x200
 for attrcheck in (0,1,0xffff):
  _,events=run(0x1f56,setup={0x3734:attrcheck});assert events==[('cursor',0,0)]+([('adjust',0,1)] if attrcheck else [])
 # Real6FEC with explicit drawing leaves observes all degenerate/reversed cases.
 border=[];m.u.mem_write(DATA+0x6200,bytes(range(0xa0,0xa8)))
 for top,left,bottom,right in [(2,3,7,11),(2,3,3,4),(2,3,2,3),(2,3,2,11),(2,3,7,3),(7,11,2,3)]:
  _,events=run(0x6fec,args=(0x6200,0x5a,(bottom<<8)|right,(top<<8)|left))
  counts=[e[1] for e in events if e[0] in ('horizontal','vertical')]
  assert counts==[((right-left)&255)-1&65535]*2+[((bottom-top)&255)-1&65535]*2
  border.append(dict(corners=[top,left,bottom,right],horizontal_count=counts[0],vertical_count=counts[2],calls=events))
 assert border[2]['horizontal_count']==border[2]['vertical_count']==65535
 # Continue the same degenerate/reversed cases through actual drawing kernels.
 #64K of addressed ES memory is a CPU model, not a claim about VGA/ROM mapping.
 actual=Machine(binaries,native_frame=True);actual.u.mem_write(DATA+0x6200,bytes(range(0xa0,0xa8)))
 native_writes=[];wraps=[];previous={}
 def primitive_entry(u,address,size,user):previous.clear()
 for entry in (0x6c20,0x8034):actual.u.hook_add(UC_HOOK_CODE,primitive_entry,begin=CODE+entry,end=CODE+entry)
 def wrote(u,access,address,size,value,user):
  assert size==2 and VIDEO<=address and address+size<=VIDEO+65536
  ip=u.reg_read(UC_X86_REG_IP);offset=address-VIDEO
  if ip in (0x6c3b,0x8058):
   if ip in previous and offset<previous[ip]:wraps.append(dict(ip=hex(ip),before=previous[ip],after=offset))
   previous[ip]=offset
  native_writes.append((offset,value))
 actual.u.hook_add(UC_HOOK_MEM_WRITE,wrote,begin=VIDEO,end=VIDEO+65535)
 full_border=[]
 for observation in border:
  top,left,bottom,right=observation['corners'];h=observation['horizontal_count'];v=observation['vertical_count']
  image=bytearray(b'\x5c\xa5'*32768);actual.u.mem_write(VIDEO,bytes(image));native_writes.clear();wraps.clear();previous.clear()
  expected_writes=[]
  def model(row,col,glyph,count=1,step=2):
   offset=2*(row*80+col)&65535
   for i in range(count):
    value=(0x5a<<8)|glyph;expected_writes.append((offset,value));struct.pack_into('<H',image,offset,value);offset=(offset+step)&65535
  model(top,left,0xa0);model(top,right,0xa2);model(bottom,right,0xa4);model(bottom,left,0xa6)
  topnext=(((top<<8)|left)+1)&65535
  model(topnext>>8,topnext&255,0xa1,h);model(bottom,(left+1)&255,0xa5,h)
  model((top+1)&255,left,0xa7,v,160);model((top+1)&255,right,0xa3,v,160)
  cases+=1;actual.run(0x6fec,args=(0x6200,0x5a,(bottom<<8)|right,(top<<8)|left))
  assert native_writes==expected_writes,(observation['corners'],len(native_writes),len(expected_writes))
  assert bytes(actual.u.mem_read(VIDEO,65536))==image
  touched={offset for offset,value in native_writes}
  full_border.append(dict(corners=observation['corners'],word_writes=len(native_writes),
   unique_word_offsets=len(touched),visible_cells_written=sum(offset<4000 for offset in touched),
   addressed_segment_min=hex(VIDEO+min(touched)),addressed_segment_max=hex(VIDEO+max(touched)),
   word_writes_outside_visible_4000_bytes=sum(offset>=4000 for offset,value in native_writes),
   di_wraps=list(wraps),video_segment_sha256=hashlib.sha256(image).hexdigest()))
 assert all(sha(ROOT/n)==digest for n,digest in identities.items()),'Sources changed during probe'
 result=dict(passed=True,cpu_cases=cases,units=units,reused_native_helpers=reused,
  sources=identities,original_comparison=original is not None,
  original_sha256=ORIGINAL if original is not None else None,border_observations=border,full_native_border=full_border,
  artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
  scope=__doc__+' Exhaustive65536 row and column values, all256 attributes; actual shared bounded/byte/optional/destination-store, clear/home/reset, physical video and border bodies execute.',
  limitations=['Operand integer reads, bytecode option reads, integer destination address, returning/aborting error policy and platform rectangle/box/cursor/erase calls are explicit controlled boundaries.',
   'Real border/coordinate/cell/horizontal/vertical/fill/stride kernels execute through finite degenerate and reversed cases with every addressed ES word observed and independently compared. The64K ES mapping is modeled RAM; physical VGA/ROM write behavior is not established.',
   'CGA input ports are modeled0/1. No physical video/BIOS timing, full DOS, compiler grammar, parent RPC, source-script composition or whole-application parity claim.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',cases,'native screen CPU cases')


if __name__=='__main__':main()
