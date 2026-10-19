#!/usr/bin/env python3
"""Execute recovered repair plus real coordinate, default, previous and video code."""
import hashlib,itertools,json,random,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attribute-repair'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Machine:
 def __init__(self):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.manifest=json.loads((OUT/'manifest.json').read_text())
  for p,h in self.manifest['sources'].items():assert sha(ROOT/p)==h
  for p,h in self.manifest['outputs'].items():assert sha(ROOT/p)==h
  for unit in self.manifest['units']:
   source=Path(unit['file']);p=OUT/(source.parent.name+'-'+source.stem+'.bin')
   self.u.mem_write(0x10000+unit['start'],p.read_bytes())
  self.u.hook_add(UC_HOOK_CODE,self.hook)
  self.u.hook_add(UC_HOOK_INSN,self.read_port,None,1,0,UC_X86_INS_IN)
 def read_port(self,u,port,size,_):
  assert port==0x3da and size==1
  self.port_reads+=1;return self.port_reads%2
 def hook(self,u,at,size,_):
  self.visited.add(at)
  if at==0x1f000:self.returned=True;u.emu_stop()
 def word(self,at,n):self.u.mem_write(0x30000+at,struct.pack('<H',n))
 def setup(self,cols,rows,flags,values,cursor,wrap=True,viewport=None,cga=False):
  self.cols=cols;self.rows=rows;self.flags=bytes(flags);self.values=bytes(values);self.cursor=cursor
  self.u.mem_write(0x30000,bytes([0xa5])*65536)
  for at,n in {0x900c:int(wrap),0x399c:cursor//cols,0x399e:cursor%cols,0x325c:cols*rows,0x3346:cursor,0x39c4:0x5000,0x39c2:0x6000,0xcdfa:0,0x3256:0,0xce2e:0,0x7a7e:79,0x7a72:cols,0x325a:cols,0x7a78:0xb800,0x7a8e:0x3da if cga else 0,0x5dea:0x40,0x5dec:0x7000}.items():self.word(at,n)
  for at,n in {0x1f70:0x9c,0x1d36:0x4e,0x1d32:0x27,0xd008:0x17}.items():self.u.mem_write(0x30000+at,bytes([n]))
  if viewport:
   active,left,right=viewport
   for at,n in {0xcdfa:1,0x3256:active,0xce2e:left,0x7a7e:right,0x7a72:80}.items():self.word(at,n)
  self.u.mem_write(0x35000,bytes(flags));self.u.mem_write(0x36000,bytes(values))
  self.video=bytearray((i*17+31)%256 for i in range(8000));self.shadow=bytearray((i*29+7)%256 for i in range(8000))
  self.u.mem_write(0xb8000,bytes(self.video));self.u.mem_write(0x70000,bytes(self.shadow))
  self.before=bytes(self.u.mem_read(0x30000,65536));self.port_reads=0
 def call(self,entry,args):
  u=self.u
  for reg,n in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xe000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x7200),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,n)
  u.mem_write(0x3e000,struct.pack('<'+'H'*(1+len(args)),0xf000,*args));self.returned=False;self.visited=set()
  u.emu_start(0x10000+entry,0,count=2000000)
  assert self.returned,'instruction limit'
  assert u.reg_read(UC_X86_REG_SP)==0xe002+len(args)*2
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000
 def reference(self,mode,wrap,viewport):
  values=bytearray(self.values);video=self.video[:];shadow=self.shadow[:];touched=[]
  if not wrap:return values,video,shadow,touched
  start=self.cursor if mode else 0
  carry=0x9c if mode==1 else (self.values[start-1] if start else self.values[0] if self.flags[0]&0x80 else 0x17)
  if not mode:carry=self.values[0] if self.flags[0]&0x80 else 0x17
  scan_mode=0 if mode==3 else mode
  # A marker at the starting cell opens a field; otherwise the next marker
  # terminates the repair after repainting that boundary cell.
  marker=not bool(self.flags[start]&0x80)
  def convert(row,col):
   visible=True;adjusted=col
   if viewport:
    active,left,right=viewport
    visible=(col<=right) if active else (left!=0 and col>=left)
    if visible and not active:adjusted-=left
   stride=80 if viewport and visible else self.cols if visible else 132
   return visible,2*(row*stride+adjusted)
  row,col=divmod(start,self.cols);visible,offset=convert(row,col)
  for i in range(start,len(values)):
   flag=self.flags[i];paint=None;stop=False
   if flag&0x80:
    if scan_mode:
     paint=0x4e if flag&1 else 0x27
     stop=marker;marker=True
    else:carry=self.values[i]
   else:
    paint=(carry&0xf8)|6 if flag&1 and not(flag&2) else carry
    values[i]=carry
   if paint is not None:
    if visible:video[offset+1]=paint
    else:shadow[0x40+offset+1]=paint
    touched.append((i,visible,paint))
   if stop:break
   col+=1
   # The native advance routine refreshes its cached visibility at the left
   # boundary and physical width, not at arbitrary right+1. Keep this quirk
   # explicit for wide/nonstandard viewport configurations.
   if viewport and col in (viewport[1],80):visible,offset=convert(row,col)
   elif col==self.cols:
    row+=1;col=0;visible,offset=convert(row,col)
   else:offset+=2
  return values,video,shadow,touched
 def verify(self,mode,wrap,viewport):
  values,video,shadow,touched=self.reference(mode,wrap,viewport)
  self.call(0x2d98,(mode,))
  after=bytes(self.u.mem_read(0x30000,65536));expected=bytearray(self.before);expected[0x6000:0x6000+len(values)]=values
  # Original callee owns its stack frame and may rewrite the mode3 argument.
  if after[:0xdf00]!=expected[:0xdf00] or after[0xe004:]!=expected[0xe004:]:
   differences=[(hex(i),after[i],expected[i]) for i in range(65536) if not 0xdf00<=i<0xe004 and after[i]!=expected[i]]
   raise AssertionError((mode,wrap,viewport,self.flags,self.cursor,differences[:12]))
  assert bytes(self.u.mem_read(0xb8000,8000))==bytes(video),(mode,wrap,viewport,'video')
  assert bytes(self.u.mem_read(0x70000,8000))==bytes(shadow),(mode,wrap,viewport,'shadow')
  if touched:
   assert 0x12c3a in self.visited
   if any(v for _,v,_ in touched):assert 0x16c84 in self.visited
  if wrap:assert 0x12b86 in self.visited
  return touched
def main():
 m=Machine();cases=0;counts=dict(repair=0,advance=0,write=0);seen=set();rng=random.Random(0x2d98)
 def case(cols,rows,flags,values,cursor,mode,wrap=True,viewport=None,cga=False):
  nonlocal cases
  m.setup(cols,rows,flags,values,cursor,wrap,viewport,cga);touched=m.verify(mode,wrap,viewport)
  seen.update(m.visited);cases+=1;counts['repair']+=1
  if cga and any(v for _,v,_ in touched):assert m.port_reads>0
 # Exhaust all combinations of native flag bits on two cells, all scan modes,
 # both starting positions and both global wrap states. High flag bits ignored.
 for flags,cursor,mode,wrap in itertools.product(itertools.product((0,1,2,3,0x80,0x81,0x82,0x83),repeat=2),(0,1),(0,1,2,3,4),(False,True)):
  case(2,1,flags,(0x92,0x35),cursor,mode,wrap)
 # Whole-plane and cross-row field patterns, including an immediate next marker,
 # no marker, first-cell default marker, and every cell being a marker.
 for cols,rows in [(1,1),(8,4),(80,25),(132,25)]:
  n=cols*rows
  patterns=[bytes(n),bytes([0x81])*n,bytes((0x80 if i%17==0 else i%4) for i in range(n)),bytes([0x80])+bytes(n-1),bytes(rng.choice((0,1,2,3,0x80,0x81)) for _ in range(n))]
  for flags,cursor,mode in itertools.product(patterns,sorted({0,min(cols-1,n-1),min(cols,n-1),n//2,n-1}),(0,1,2,3)):
   values=bytes((i*31+0x17)&255 for i in range(n));case(cols,rows,flags,values,cursor,mode)
 # Actual hidden shadow writes and visible native byte writes across viewport
 # transitions; retain the recovered inactive-left0 underflow behavior.
 for active,left,right,cursor,mode in itertools.product((0,1),(0,40),(79,119),(0,39,40,79,80,131,132,263),(0,1,2,3)):
  flags=bytes(0x80 if i%37==0 else i%4 for i in range(264));values=bytes((i*7+11)&255 for i in range(264))
  case(132,2,flags,values,cursor,mode,viewport=(active,left,right))
 # CGA status reads use the actual native polling loop, with an explicit fake
 # retrace port; no physical video timing claim follows.
 for mode in range(4):case(8,2,bytes([0x80])+bytes(15),bytes(range(16)),3,mode,cga=True)
 # Direct advance tests distinguish crossing a row from a viewport boundary.
 for viewport,row,col in itertools.product((None,(0,40,119),(1,40,79)),(0,2),(0,39,40,79,80,131)):
  cols=132 if viewport else 80
  if col>=cols:continue
  m.setup(cols,4,bytes(cols*4),bytes(cols*4),0,viewport=viewport)
  # A valid converted descriptor supplies native cached video-byte offset.
  m.u.mem_write(0x3e100,struct.pack('<4H',0,row,col,0));m.call(0x2b86,(0xe100,))
  before=struct.unpack('<4H',m.u.mem_read(0x3e100,8));m.call(0x2cf2,(0xe100,))
  newrow,newcol=(row+1,0) if col+1==cols else (row,col+1)
  # Exact native viewport boundaries recalculate the visibility and offset.
  recalc=(viewport and newcol in (viewport[1],80)) or newcol==0
  if recalc:
   visible=True;adjusted=newcol
   if viewport:
    active,left,right=viewport;visible=newcol<=right if active else left!=0 and newcol>=left
    if visible and not active:adjusted-=left
   expected=(int(visible),newrow,newcol,2*(newrow*(80 if viewport and visible else cols if visible else 132)+adjusted))
  else:expected=(before[0],newrow,newcol,(before[3]+2)&65535)
  assert struct.unpack('<4H',m.u.mem_read(0x3e100,8))==expected
  seen.update(m.visited);cases+=1;counts['advance']+=1
 # Direct writer: respects the descriptor's visible flag only in viewport mode.
 for viewport,visible,offset,paint in itertools.product((False,True),(0,1),(1,159,3999),(0,0x27,0xfe)):
  m.setup(80,25,bytes(2000),bytes(2000),0,viewport=(1,0,79) if viewport else None)
  m.u.mem_write(0x3e100,struct.pack('<4H',visible,0,0,offset));m.call(0x2c3a,(0xe100,paint))
  video=m.video[:];shadow=m.shadow[:]
  if viewport and not visible:shadow[0x40+offset]=paint
  else:video[offset]=paint
  assert bytes(m.u.mem_read(0xb8000,8000))==bytes(video)
  assert bytes(m.u.mem_read(0x70000,8000))==bytes(shadow)
  seen.update(m.visited);cases+=1;counts['write']+=1
 for entry in (0x12d98,0x12c3a,0x12cf2,0x12b86,0x12d38,0x12d4c,0x16c84):assert entry in seen,hex(entry)
 report=dict(passed=True,cases=cases,groups=counts,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),native_entries_executed=[hex(e) for e in (0x2d98,0x2c3a,0x2cf2,0x2b86,0x2d38,0x2d4c,0x6c84)],original_inputs=[],production_integration=False,scope='All seven real recovered routines execute. Reference checks full metadata/value guards, character/attribute video and shadow bytes, native early marker termination, mode3 tail repair, row/viewport transitions and callee stack/register ABI. Only CGA retrace port reads are modeled. Application protected scrolling and physical hardware remain unverified.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Attribute repair',cases,'cases PASS',counts)
if __name__=='__main__':main()
