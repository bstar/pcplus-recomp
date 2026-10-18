#!/usr/bin/env python3
"""Actual far packed-screen helpers, nested owners and CGA memory/port boundary."""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from unicorn.x86_const import *
from check_transport import Transport,ROOT,BINARY
from terminal_memory import inspect_terminal_memory

class Screens(Transport):
 def __init__(self):
  super().__init__();self.cga_reads=0
 def input_port(self,u,port,size,data):
  if port in (0x3da,0x3ba):
   assert size==1;value=self.cga_reads%2;self.cga_reads+=1;return value
  return super().input_port(u,port,size,data)
 def invoke(self,name,*,count=2000,video=0,buffer='browser_screen',offset=None,segment=None):
  start=self.symbols[buffer];segment=self.get(buffer+'_segment') if segment is None else segment
  position=start-segment*16 if offset is None else offset
  regs={UC_X86_REG_CS:self.base_segment,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:self.ds,UC_X86_REG_AX:count,UC_X86_REG_BX:0x1234,UC_X86_REG_CX:0x2345,UC_X86_REG_DX:video,UC_X86_REG_SI:position,UC_X86_REG_DI:position,UC_X86_REG_ES:segment,UC_X86_REG_BP:0x3456}
  for r,v in regs.items():self.uc.reg_write(r,v)
  sp=self.offset('terminal_stack_top')-2;self.uc.mem_write(self.data_base+sp,struct.pack('<H',self.return_offset));self.uc.reg_write(UC_X86_REG_SP,sp);self.uc.reg_write(UC_X86_REG_EFLAGS,0x202)
  self.returned=False;self.uc.emu_start(self.symbols[name],0,count=1000000)
  assert self.returned and self.uc.reg_read(UC_X86_REG_SP)==sp+2
  for r,v in regs.items():assert self.uc.reg_read(r)==v,(name,r,self.uc.reg_read(r),v)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x200
  return bool(self.uc.reg_read(UC_X86_REG_EFLAGS)&1)
 def save(self,**kw):return self.invoke('terminal_screen_save_far',**kw)
 def restore(self,**kw):return self.invoke('terminal_screen_restore_far',**kw)
def packed(raw):return b''.join(raw[i:i+2][::-1] for i in range(0,len(raw),2))
def main():
 cases=[]
 def check(name,fn):
  n=fn();cases.append(dict(case=name,inputs=n,passed=True));print(name,'PASS',n,flush=True)
 def all_cells():
  m=Screens();raw=bytes((i*37+i//160)%256 for i in range(4000));address=m.symbols['browser_screen']
  m.uc.mem_write(0xb8000,raw);assert not m.save();assert bytes(m.uc.mem_read(address,4000))==packed(raw)
  m.uc.mem_write(0xb8000,b'\x99'*4000);assert not m.restore();assert bytes(m.uc.mem_read(0xb8000,4000))==raw
  return 2000
 check('all2000-raw-character-attribute-cells-native-packed-order-NUL-SUB-highbytes',all_cells)
 def nesting():
  m=Screens();a=b'A\x1e'*2000;b=b'B\x2f'*2000
  m.uc.mem_write(0xb8000,a);assert not m.save()
  m.uc.mem_write(0xb8000,b);assert not m.save(buffer='ed_screen')
  assert bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))==packed(a)
  m.uc.mem_write(0xb8000,b'C\x4f'*2000);assert not m.restore(buffer='ed_screen');assert bytes(m.uc.mem_read(0xb8000,4000))==b
  assert not m.restore();assert bytes(m.uc.mem_read(0xb8000,4000))==a
  assert m.get('browser_screen_segment')==m.get('ed_screen_segment')!=m.ds
  return 2
 check('independent-browser-editor-far-owners-restore-nested-LIFO-without-alias',nesting)
 def video_modes():
  for segment,offset,cga in ((0xb800,8192,0),(0xb000,4096,0),(0xb800,0,0x3da),(0xb000,0,0x3ba),(0xb800,61536,0)):
   m=Screens();m.put('text_video_segment',segment);m.put('text_cga_status_port',cga)
   address=segment*16+offset;raw=b'X\x37'*2000;m.uc.mem_write(address,raw)
   assert not m.save(video=offset);assert bytes(m.uc.mem_read(m.symbols['browser_screen'],4000))==packed(raw)
   m.uc.mem_write(address,b'\0'*4000);assert not m.restore(video=offset);assert bytes(m.uc.mem_read(address,4000))==raw
   if cga:assert m.cga_reads==12000,m.cga_reads
  return 5
 check('active-page-monochrome-exact64K-video-end-and-native-CGA-polling',video_modes)
 def buffer_end():
  for count,offset in ((2000,61536),(1,65534)):
   m=Screens();raw=b'Z\x7f'*count;address=0x60000+offset
   m.uc.mem_write(0xb8000,raw);m.uc.mem_write(address-1,b'\xa5');m.uc.mem_write(0x70000,b'\x5a')
   assert not m.save(count=count,offset=offset,segment=0x6000)
   assert bytes(m.uc.mem_read(address,len(raw)))==packed(raw)
   m.uc.mem_write(0xb8000,b'\0'*len(raw));assert not m.restore(count=count,offset=offset,segment=0x6000)
   assert bytes(m.uc.mem_read(0xb8000,len(raw)))==raw
   assert bytes(m.uc.mem_read(address-1,1))==b'\xa5' and bytes(m.uc.mem_read(0x70000,1))==b'\x5a'
  return 2
 check('allocated-caller-far-buffer-ending-at64K-no-wrap-or-canary-write',buffer_end)
 def bounds():
  m=Screens();m.put('text_cga_status_port',0x3da);original_video=bytes(m.uc.mem_read(0xb8000,65536));original_buffers=bytes(m.uc.mem_read(m.symbols['browser_screen'],12000))
  bad=[dict(count=2001),dict(count=65535),dict(video=61537),dict(offset=61537),dict(count=1,video=65535),dict(count=1,offset=65535)]
  for fn in (m.save,m.restore):
   for args in bad:
    assert fn(**args);assert bytes(m.uc.mem_read(0xb8000,65536))==original_video
    assert bytes(m.uc.mem_read(m.symbols['browser_screen'],12000))==original_buffers
   assert not fn(count=0,video=65535,offset=65535)
  assert not m.cga_reads
  return 14
 check('count-video-buffer-wrap-denied-before-I-O-and-zero-count-noop',bounds)
 def layout():
  mp=ROOT/'build/terminal/terminal.map';listing=mp.read_text();image=BINARY.read_bytes();header=struct.unpack_from('<14H',image);start=header[4]*16
  m=Screens();good=inspect_terminal_memory(BINARY,mp);assert good['far_ui_storage_bytes']==12000
  def file_at(name):return start+m.symbols[name]-m.base
  mutants=[]
  for name in ('browser_screen','ed_screen','program_screen'):
   pointer=file_at(name+'_segment');bad=bytearray(image);bad[pointer]^=1
   mutants.append((name+'-wrong-segment',bad,listing,'invalid relocated segment pointer'))
   bad=bytearray(image);wanted=pointer-start
   for i in range(header[3]):
    off,seg=struct.unpack_from('<HH',bad,header[12]+i*4)
    if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+i*4,0,0);break
   else:raise AssertionError('Missing original UI relocation')
   mutants.append((name+'-missing-relocation',bad,listing,'invalid relocated segment pointer'))
  def mapped(changes):
   lines=[]
   for line in listing.splitlines():
    if re.match(r'^[0-9a-f]{4}:[0-9a-f]{4}',line,re.I) and line.split()[-1] in changes:
     seg,off=changes[line.split()[-1]];line=f'{seg:04x}:{off:04x}'+line[9:]
    lines.append(line)
   return '\n'.join(lines)+'\n'
  b=good['ui_screen_buffers']['browser_screen'];e=good['ui_screen_buffers']['ed_screen']
  alias=mapped({'ed_screen':(b['relative_segment'],b['offset']),'ed_screen_end':(b['relative_segment'],b['offset']+4000)})
  mutants.append(('nested-owners-alias',image,alias,'nested owners alias'))
  short=mapped({'ed_screen_end':(e['relative_segment'],e['offset']+3999)})
  mutants.append(('truncated-owner',image,short,'invalid UI screen extent'))
  with tempfile.TemporaryDirectory() as folder:
   exe=Path(folder)/'BAD.EXE';badmap=Path(folder)/'bad.map'
   for label,data,text,reason in mutants:
    exe.write_bytes(data);badmap.write_text(text)
    try:inspect_terminal_memory(exe,badmap)
    except AssertionError as error:assert reason in str(error),(label,error)
    else:raise AssertionError(('Invalid layout accepted',label))
  return len(mutants)
 check('three-relocated-private-owners-and-eight-invalid-layouts-rejected',layout)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_ui_screen_far.py','src/terminal/ui_screen_far.asm']},scope='Real linked far screen helpers and recovered packed-cell read/write routines with modeled memory/CGA ports; all registers and DS=SS ABI checked. Literal cells, nested owners, pages, monochrome and exact64K/overflow boundaries verified. Actual DOS browser/editor/PROGRAM and retained allocation are separate tests; physical CGA timing is not established.')
 (ROOT/'build/terminal/ui-screen-far-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
