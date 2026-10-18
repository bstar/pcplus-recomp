#!/usr/bin/env python3
"""Run maintained clipboard code, optionally compare genuine resident routines."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/clipboard'
class Clipboard(DosImage):
 def __init__(self):
  super().__init__(OUT/'CLIPCORE.EXE',OUT/'clipboard.map')
  self.s=self.stage_near(b'\xa5'*1024);self.row=self.s+256;self.out=self.s+400;self.first=self.s+416;self.past=self.s+418;self.packet=self.s+448;self.size=self.s+648
  assert self.call('_clip_initialize',[self.s])==0
 def read(self,offset,n):return bytes(self.uc.mem_read(self.data_base+offset,n))
 def write(self,offset,data):self.uc.mem_write(self.data_base+offset,data)
 def state(self):return self.read(self.s,214)
 def change(self,operation,index=0,text=None):
  pointer=0
  if text is not None:self.write(self.row,text+b'\0');pointer=self.row
  return self.call('_clip_change',[self.s,operation,index,pointer])
 def extract(self,row,dot,width=None):
  width=len(row) if width is None else width;self.write(self.row,row)
  self.write(self.out,b'Q'*13);self.write(self.first,b'\x11\x11\x22\x22')
  status=self.call('_clip_extract',[self.row,width,dot,self.out,self.first,self.past])
  return status,self.read(self.out,13).split(b'\0')[0],struct.unpack('<HH',self.read(self.first,4))
 def prepare(self,mode,capacity=196):
  self.write(self.packet,b'Q'*200);self.write(self.size,b'\x55\x55')
  status=self.call('_clip_prepare',[self.s,mode,self.packet,capacity,self.size])
  n=int.from_bytes(self.read(self.size,2),'little')
  return status,self.read(self.packet,n) if n<=196 else None,n

def native_model():
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
 assert hashlib.sha256(image).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 sys.path.insert(0,str(ROOT/'reconstruction'))
 from check_ansi_freeze import load_image
 u=load_image(image);base=0x1fb70
 overlay_manifest=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())
 assert overlay_manifest['source_sha256']==hashlib.sha256(image).hexdigest()
 overlay=next(x for x in overlay_manifest['overlays'] if x['id']==15)
 raw=image[overlay['source_file_offset']:overlay['source_file_offset']+overlay['initialized_bytes']]
 assert hashlib.sha256(raw).hexdigest()==overlay['sha256'] and not overlay['relocation_records']
 u.mem_write(0x10000+overlay['relative_load_segment']*16,raw)
 wire=bytearray();selector=[1]
 done=[]
 def stop(uc,address,size,_):
  if address==0x1eff0:done.append(True);uc.emu_stop();return
  # UI/beep and transmitter boundaries only. Genuine dispatch, CR helper and the
  # SINGLE compaction memmove routines execute normally from original bytes.
  if address in (0x16bbe,0x1d0d0,0x13226,0x1376d,0x14870,0x1abac,0x1ab0b):
   sp=uc.reg_read(UC_X86_REG_SP);stack=base+sp;back=int.from_bytes(uc.mem_read(stack,2),'little');pop=2
   if address==0x1d0d0:uc.reg_write(UC_X86_REG_AX,selector[0])
   elif address==0x16bbe:uc.reg_write(UC_X86_REG_AX,0);uc.reg_write(UC_X86_REG_DX,0)
   elif address==0x14870:pop=6
   elif address in (0x1abac,0x1ab0b):
    arg=int.from_bytes(uc.mem_read(stack+2,2),'little');pop=4
    if address==0x1ab0b:wire.append(arg&255)
    else:
     for i in range(13):
      byte=uc.mem_read(base+arg+i,1)[0]
      if not byte:break
      wire.append(byte)
     else:raise AssertionError('Original string emitter received an unterminated slot')
   uc.reg_write(UC_X86_REG_SP,sp+pop);uc.reg_write(UC_X86_REG_IP,back)
 u.hook_add(UC_HOOK_CODE,stop)
 def run(address,arg):
  done.clear();u.mem_write(base+0xf000,struct.pack('<HH',0xeff0,arg))
  for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x1fb7),(UC_X86_REG_SS,0x1fb7),(UC_X86_REG_SP,0xf000),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
  u.emu_start(address,0,count=100000)
  assert done and u.reg_read(UC_X86_REG_SP)==0xf002,(hex(address),done,hex(u.reg_read(UC_X86_REG_CS)),hex(u.reg_read(UC_X86_REG_IP)),hex(u.reg_read(UC_X86_REG_SP)),hex(u.reg_read(UC_X86_REG_BP)))
  return u.reg_read(UC_X86_REG_AX)
 def byte(value):return run(0x139fc,value)==0
 def extract(row,dot):
  u.mem_write(base+0x9000,b' '+row+b' ');u.mem_write(base+0xce6a,b'Q'*13)
  result=run(0x1397b,0x9001+dot)
  text=bytes(u.mem_read(base+0xce6a,13)).split(b'\0')[0]
  return bool(result),text,(result-0x9001 if result else None)
 def packet(state,mode):
  wire.clear();selector[0]=[2,1,3][mode]
  u.mem_write(base+0x7580,state[:2]);u.mem_write(base+0x206e,state[2:4]);u.mem_write(base+0xe798,state[4:199]);u.mem_write(base+0xe85c,state[199:214])
  run(0x1d34e,0)
  after=bytes(u.mem_read(base+0x7580,2))+bytes(u.mem_read(base+0x206e,2))+bytes(u.mem_read(base+0xe798,195))+bytes(u.mem_read(base+0xe85c,15))
  return bytes(wire),after
 return byte,extract,packet

def main(original=False):
 groups=[];native_byte,native_extract,native_packet=native_model() if original else (None,None,None);comparisons=0
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def predicates():
  nonlocal comparisons
  m=Clipboard();blacklist=b'."/\\[]:|<>+=;,'
  for value in range(256):
   want=33<=value<=126 and value not in blacklist
   assert m.call('_clip_valid_byte',[value])==int(want)
   if native_byte:assert native_byte(value)==want;comparisons+=1
  return 256
 check('all256-original-screen-byte-predicate-values',predicates)
 rows=[b'A.Z',b'FOO.ZIP',b'ABCDEFGH.123',b'ABCDEFGHI.ZIP',b'.ZIP',b'FOO.',b'FOO. ',b'[foo.zip]',b'C:\\a.zip',b'foo.longextension',b'ONE.TWO.THREE',b'NOEXTENSION',b'\x82ABC.ZIP',b'ABC.\x82ZIP',b'ABC.X\x82',b'A'*120+b' B.ZIP',b'B.ZIP'+b' '*127]
 def extraction():
  nonlocal comparisons
  count=0;m=Clipboard()
  for row in rows:
   for dot,value in enumerate(row):
    if value!=46:continue
    status,name,(first,past)=m.extract(row,dot)
    expected={
     (b'A.Z',1):(b'A.Z',0,3), (b'FOO.ZIP',3):(b'FOO.ZIP',0,7),
     (b'ABCDEFGH.123',8):(b'ABCDEFGH.123',0,12),
     (b'[foo.zip]',4):(b'foo.zip',1,8), (b'C:\\a.zip',4):(b'a.zip',3,8),
     (b'foo.longextension',3):(b'foo.lon',0,7),
     (b'ONE.TWO.THREE',3):(b'ONE.TWO',0,7), (b'ONE.TWO.THREE',7):(b'TWO.THR',4,11),
     (b'\x82ABC.ZIP',4):(b'ABC.ZIP',1,8), (b'ABC.X\x82',3):(b'ABC.X',0,5),
     (b'A'*120+b' B.ZIP',122):(b'B.ZIP',121,126), (b'B.ZIP'+b' '*127,1):(b'B.ZIP',0,5)}.get((row,dot))
    if expected is None:assert (status,name,(first,past))==(7,b'Q'*13,(0x1111,0x2222)),(row,dot,status,name)
    else:assert (status,name,first,past)==(0,*expected),(row,dot,status,name,first,past,expected)
    if native_extract:
     ok,text,start=native_extract(row,dot);assert (status==0)==ok,(row,dot,status,ok)
     if ok:assert name==text and first==start and past==start+len(text),(row,dot,name,text,first,start,past)
     else:assert name==b'Q'*13 and (first,past)==(0x1111,0x2222)
     comparisons+=1
    count+=1
  for row,dot,want,span in [(b'[foo.zip]',4,b'foo.zip',(1,8)),(b'foo.longextension',3,b'foo.lon',(0,7)),(b'FIRST.ZIP SECOND.ARJ',16,b'SECOND.ARJ',(10,20))]:
   assert m.extract(row,dot)==(0,want,span);count+=1
  for row,dot in [(b'.ZIP',0),(b'123456789.ZIP',9),(b'FOO.',3),(b'FOO. ',3)]:
   assert m.extract(row,dot)==(7,b'Q'*13,(0x1111,0x2222));count+=1
  return count
 check('bounded-132-column-filename-extraction-long-extension-truncation-and-row-edges',extraction)
 def mutations():
  m=Clipboard();assert m.change(0,text=b'foo.zip   ')==0;assert m.state()[4:17].startswith(b'FOO.ZIP\0')
  before=m.state();assert m.change(0,text=b'FoO.ZiP')==4 and m.state()==before
  assert m.change(0,text=b'two.arj')==0
  assert m.change(1,1,b'FOO.ZIP')==0 and m.state()[4:17]==m.state()[17:30]
  assert m.change(1,0,b'lower.zip  ')==0 and m.change(0,text=b'lower.zip')==0
  assert m.change(1,1,b'')==0 and int.from_bytes(m.state()[:2],'little')==3
  assert m.change(4,2)==0 and m.state()[199+2]==16
  before=m.state();status,data,n=m.prepare(2);assert (status,data)==(0,b'LOWER.ZIP\r\r') and m.state()==before
  assert m.prepare(1)[:2]==(0,b'lower.zip\r\rLOWER.ZIP\r\r')
  assert m.prepare(0)[:2]==(0,b'lower.zip\r') and m.state()==before
  assert m.change(2,0)==0 and m.prepare(0)[:2]==(0,b'\r')
  assert m.change(5,32)==0 and m.change(3)==0 and m.state()==b'\0\0 \0'+b'\0'*210
  assert m.prepare(2)[:2]==(0,b'')
  return 13
 check('original-add-uppercase-duplicate-check-edit-case-duplicates-holes-single-tag-and-purge',mutations)
 def packets():
  m=Clipboard()
  for i in range(15):assert m.change(0,text=bytes([65+i])+b'BCDEFGH.ZIP')==0
  before=m.state();assert m.change(0)==3 and m.state()==before
  status,data,n=m.prepare(1,195);assert status==6 and n==0x5555 and m.read(m.packet,200)==b'Q'*200 and m.state()==before
  for separator in range(256):
   assert m.change(5,separator)==0
   want=b''.join(bytes([65+i])+b'BCDEFGH.ZIP'+bytes([separator]) for i in range(15))+b'\r'
   assert len(want)==196 and m.prepare(1)==(0,want,196)
   assert m.read(m.packet+196,4)==b'Q'*4
  return 258
 check('full15-entry-196-byte-packet-all256-separators-and-capacity-atomicity',packets)
 def packet_oracle():
  nonlocal comparisons
  cases=0
  for names in ([],[b'ONE.ZIP'],[b'',b'lower.zip',b''],[bytes([65+i])+b'BCDEFGH.ZIP' for i in range(15)]):
   for separator in (0,13,32,255):
    for mode in range(3):
     m=Clipboard()
     # Construct valid allocated holes through the original add/edit policy.
     for i,name in enumerate(names):
      assert m.change(0,text=(name or b'TEMP.ZIP'))==0
      assert m.change(1,i,name)==0
      if i%2==0:assert m.change(4,i)==0
     assert m.change(5,separator)==0
     before=m.state();status,data,n=m.prepare(mode);assert status==0 and m.state()==before
     selected=[x for i,x in enumerate(names) if mode==1 or i%2==0]
     want=(names[0]+b'\r' if names else b'') if mode==0 else (b''.join(x+bytes([separator]) for x in selected)+b'\r' if selected else b'')
     assert data==want,(names,mode,separator,data,want)
     if native_packet:
      packet,after=native_packet(before,mode);assert packet==data,(names,mode,separator,packet,data)
      if mode==0 and names:
       assert m.change(2,0)==0
       def logical(s):return s[:4],tuple(s[4+i*13:17+i*13].split(b'\0')[0] for i in range(15)),s[199:214]
       assert logical(after)==logical(m.state())
      else:assert after==before
      comparisons+=1
     cases+=1
  return cases
 check('allocated-empty-entry-separators-all-tagged-single-packet-and-single-commit-oracle',packet_oracle)
 def bounds():
  m=Clipboard();before=m.state();assert m.change(99)==1 and m.state()==before
  assert m.change(0,text=b'X'*13)==1 and m.state()==before
  for pointer in (0,0xfff0):assert m.call('_clip_initialize',[pointer])==1
  for offset,value in [(0,16),(4,b'X'*13)]:
   m=Clipboard();m.write(m.s+offset,value.to_bytes(2,'little') if isinstance(value,int) else value);before=m.state()
   assert m.change(3)==2 and m.state()==before
  m=Clipboard();assert m.change(0,text=b'FOO.ZIP')==0;before=m.state()
  for output,size in [(m.s,m.size),(m.packet,m.s),(m.size,m.size),(0xfffc,m.size)]:
   m.write(m.size,b'\x55\x55');assert m.call('_clip_prepare',[m.s,1,output,196,size])==1 and m.state()==before
  for args in [(m.row,133,1,m.out,m.first,m.past),(m.row,10,10,m.out,m.first,m.past),(m.row,10,1,m.row,m.first,m.past),(m.row,10,1,m.out,m.first,m.first),(0xfffe,10,1,m.out,m.first,m.past)]:
   m.write(m.out,b'Q'*13);m.write(m.first,b'\x11\x11\x22\x22');assert m.call('_clip_extract',args)==1
   assert m.read(m.out,13)==b'Q'*13 and m.read(m.first,4)==b'\x11\x11\x22\x22'
  return 15
 check('null-wrapped-overlong-malformed-state-and-overlapping-output-rejection',bounds)
 result=dict(passed=True,binary_sha256=hashlib.sha256((OUT/'CLIPCORE.EXE').read_bytes()).hexdigest(),inputs=sum(g['inputs'] for g in groups),sources={**json.loads((OUT/'manifest.json').read_text())['sources'],'standalone/check_clipboard.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},cases=groups,original_comparisons=comparisons,original_sha256='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904' if original else None,scope='Actual linked maintained DOS16 clipboard core. Optional controlled genuine resident39FC/397B and raw original overlay15 D34E replay includes actual original CRT string helpers/compaction. UI/string-emitter/byte-emitter boundaries are declared; no physical-wire claim. No original startup or synthetic analysis EXE execution; no live UI/UART/transfer integration claim.')
 (OUT/('original-checks.json' if original else 'linked-checks.json')).write_text(json.dumps(result,indent=2)+'\n');print('Clipboard core:',result['inputs'],'inputs,',comparisons,'original comparisons')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--original',action='store_true');main(parser.parse_args().original)
