#!/usr/bin/env python3
"""Actual linked KEY code and optional genuine-original replay at explicit services."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/meta-keys';PROOF=json.loads((ROOT/'reconstruction/meta_keys/provenance.json').read_text())
class Meta(DosImage):
 def __init__(self,original=False):
  super().__init__(OUT/'METAKEYS.EXE',OUT/'meta_keys.map');self.original=original
  if original:
   sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
   data=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(data).hexdigest()==PROOF['source_sha256']
   self.uc=load_image(data);self.ds=0x1fb7;self.data_base=self.ds*16
   self.symbols={name:self.data_base+int(at,16) for at,name in PROOF['state'].items()}
   for unit in PROOF['units']:
    name={'invoke':'meta_keys_invoke','text':'meta_keys_send_text','caret':'meta_keys_expand','alt_digit':'meta_keys_alt_digit','hook':'meta_keys_hook','tick_delay':'meta_keys_tick_delay'} .get(Path(unit['file']).stem)
    if name:self.symbols[name]=0x10000+unit['start']
   self.symbols.update({'test_input':self.data_base+0x5000,'test_output':self.data_base+0x5200})
   self.uc.hook_add(UC_HOOK_CODE,self._stop)
  self.events=[];self.ticks=0
  self.put('meta_script_active',0);self.put('meta_pacing',0);self.put('meta_local_echo',0);self.put('meta_pause_byte',ord('~'),1)
  self.uc.mem_write(self.symbols['meta_actions'],bytes(540));self.uc.hook_add(UC_HOOK_CODE,self.boundaries)
 def cstring(self,offset):
  data=bytes(self.uc.mem_read(self.data_base+offset,512));assert b'\0' in data
  return data.split(b'\0')[0]
 def ret(self,cleanup=0,value=None):
  uc=self.uc;sp=uc.reg_read(UC_X86_REG_SP);ip=struct.unpack('<H',uc.mem_read(self.data_base+sp,2))[0]
  uc.reg_write(UC_X86_REG_SP,sp+2+cleanup);uc.reg_write(UC_X86_REG_IP,ip)
  if value is not None:uc.reg_write(UC_X86_REG_AX,value)
 def boundaries(self,uc,address,size,_):
  services={'meta_keys_transmit':0xab0b,'meta_keys_echo':0x610,'meta_keys_message':0x427f,'meta_keys_aspect_service':0x4b1f,'meta_keys_program_service':0x433d,'meta_keys_resolve_program':0x353d}
  for name,offset in services.items():
   target=0x10000+offset if self.original else self.symbols[name]
   if address!=target:continue
   sp=uc.reg_read(UC_X86_REG_SP);args=struct.unpack('<5H',uc.mem_read(self.data_base+sp+2,10))
   if name=='meta_keys_transmit':self.events.append(('wire',args[0]&255));self.ret(2)
   elif name=='meta_keys_echo':self.events.append(('echo',args[0]&255));self.ret()
   elif name=='meta_keys_message':self.events.append(('message',self.cstring(uc.reg_read(UC_X86_REG_BX))));self.ret()
   elif name=='meta_keys_aspect_service':self.events.append(('aspect',args[0],self.cstring(args[1])));self.ret(4,0)
   elif name=='meta_keys_resolve_program':self.events.append(('resolve',self.cstring(args[0])));self.ret(value=args[0])
   else:
    self.events.append(('program',self.cstring(args[0]),None if not args[1] else self.cstring(args[1]),*args[2:]))
    self.ret(value=0x1234)
   return
  # Each actual CMP observes one new BIOS transition; model has no wall time.
  if address==self.symbols['meta_keys_tick_delay']+0x11:
   self.ticks+=1;uc.mem_write(0x46c,struct.pack('<H',self.ticks&0xffff))
 def input(self,data):self.uc.mem_write(self.symbols['test_input'],data+b'\0'+bytes(255-len(data)));return self.offset('test_input')
 def expand(self,data,extent=None):
  ptr=self.input(data);self.uc.mem_write(self.symbols['test_output'],b'\xcc'*256)
  self.call('meta_keys_expand',[ptr,self.offset('test_output')])
  return bytes(self.uc.mem_read(self.symbols['test_output'],extent or 128))
 def invoke(self,text,kind,context=3):
  self.call('meta_keys_invoke',[self.input(text),kind,context]);return self.events

def run(original=False):
 counts=0;original_count=0;groups=[]
 def both(fn):
  nonlocal counts,original_count
  a=fn(Meta());counts+=1
  if original:
   b=fn(Meta(True));assert a==b,(a,b);original_count+=1
  return a
 for text,want in [(b'',b''),(b'plain',b'plain'),(b'^M^J',b'\r\n'),(b'^@',b'\xff'),(b'^^',b'\x1e'),(b'^^^',b'^'),(b'^^^^',b'^\0'),(b'^a^z',b'\x01\x1a'),(b'^?',b'\x1f'),(b'^`ABC',b'\0ABC'),(b'A^\0Q',b'A\0Q')]:
  # Add an extra terminator for malformed trailingcaret observation without
  # permitting an unbounded CPU read. Original parser still crosses firstNUL.
  def expand(m,text=text,want=want):
   actual=m.expand(text,len(want)+1);assert actual==want+b'\0',(text,actual,want);return actual
  both(expand)
 for operand in range(1,256):
  def operand_case(m,operand=operand):
   output=0xff if operand==0x40 else operand&0x1f
   actual=m.expand(b'^'+bytes([operand]),2);assert actual==bytes([output,0]);return actual
  both(operand_case)
 groups.append('exact-caret-grammar-triple-caret-NUL-and-trailing-caret-overread')
 for text,echo,pause,wire,ticks in [(b'^@A~B',0,ord('~'),[0,65,66],10),(b'~',1,ord('~'),[],10),(b'^@',1,0xff,[],10),(b'^^^',1,ord('~'),[94],0),(b'^`LOST',1,ord('~'),[],0),(b'A^MB',1,ord('~'),[65,13,66],0)]:
  def send(m,text=text,echo=echo,pause=pause,wire=wire,ticks=ticks):
   m.put('meta_local_echo',echo);m.put('meta_pause_byte',pause,1);m.invoke(text,3)
   actual=[v for event,v in m.events if event=='wire'];assert actual==wire,(text,m.events)
   echoed=[v for event,v in m.events if event=='echo'];assert echoed==([v for v in wire if v!=0] if echo else [])
   assert m.ticks==ticks
   return m.events,m.ticks
  both(send)
 groups.append('TEXT-pause-precedence-ten-BIOS-ticks-NUL-local-echo-and-stop')
 for active in (0,1):
  def aspect(m,active=active):
   m.put('meta_script_active',active);m.invoke(b'LOGIN.ASP',0)
   assert m.events==([('message',b'Already in script file.  Chain not permitted')] if active else [('aspect',0,b'LOGIN.ASP')]);return m.events
  both(aspect)
 def program(m):
  m.invoke(b'VIEW.EXE /Q',1);assert m.events==[('program',b'VIEW.EXE /Q',None,1,1,1)];return m.events
 both(program)
 for kind in (4,0xffff):
  def unknown(m,kind=kind):m.invoke(b'ignored',kind);assert not m.events;return m.events
  both(unknown)
 groups.append('ASPECT-active-script-guard-PROGRAM-flags-unknown-kind-no-action')
 for mode in (0,1):
  for context in (3,0x7fff,0xffff):
   def hook(m,mode=mode,context=context):
    # Call original callee-cleanup hook through real source bridge for linked
    # image; original CPU uses an equivalent caller fixture below.
    ptr=m.input(b'HOOK.EXE');m.uc.mem_write(m.symbols['test_output'],b'ARG\0')
    args=[mode,m.offset('test_output'),context,ptr]
    if m.original:
     uc=m.uc
     for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:uc.reg_write(reg,value)
     sp=0xe000;uc.mem_write(m.data_base+sp,struct.pack('<5H',0xf000,*args));uc.reg_write(UC_X86_REG_SP,sp);m.returned=False;uc.emu_start(m.symbols['meta_keys_hook'],0,count=100000);assert m.returned and uc.reg_read(UC_X86_REG_SP)==sp+10
    else:m.call('meta_hook_call',args)
    signed=context if context<0x8000 else context-0x10000
    packed=lambda name:str((m.ds<<16)|m.offset(name)).encode()
    command=b' PCPLUS '+(packed('meta_hook_exchange_a')+b' '+packed('meta_hook_exchange_b')+b' ' if mode else b'')+packed('meta_prm_image')+b' '+str(signed).encode()+(b' ARG' if not mode else b'')
    assert m.events==[('resolve',b'HOOK.EXE'),('program',b'HOOK.EXE',command,0,0,0)],m.events
    assert m.get('meta_hook_result')==0x1234
    # Packed addresses intentionally differ after relocation; compare semantic
    # shape/return/argument modes rather than falsely demand identical pointers.
    return mode,signed,m.get('meta_hook_result'),len(m.events)
   both(hook)
 for text in (b'',b'[NONE]'):
  def invalid(m,text=text):
   m.invoke(text,2);assert m.get('meta_hook_result')==1 and m.events==[('message',b'No program name specified')];return m.events,m.get('meta_hook_result')
  both(invalid)
 groups.append('HOOK-packed-far-pointer-protocol-signed-context-mode-arguments-and-name-guard')
 for index in range(10):
  def alt(m,index=index):
   text=bytes([65+index]);record=struct.pack('<H',3)+text+b'\0'+bytes(50);m.uc.mem_write(m.symbols['meta_actions']+54*index,record);m.put('meta_normalized_scan',0x78+index);m.call('meta_keys_alt_digit');assert m.events==[('wire',65+index)];return m.events
  both(alt)
 def alt_hook(m):
  m.uc.mem_write(m.symbols['meta_actions']+54,struct.pack('<H',2)+b'HOOK.EXE\0'+bytes(43));m.put('meta_normalized_scan',0x79);m.call('meta_keys_alt_digit')
  event=m.events[-1];assert event[0]=='program' and event[2].endswith(b' 3') and event[3:]==(0,0,0)
  return event[0],event[1],event[2].split()[-1],event[3:]
 both(alt_hook)
 def calibrated(m):
  m.put('meta_pacing',3);m.put('meta_pace_counter',0);m.put('meta_pace_calibration',1);m.invoke(b'AB',3);assert m.events==[('wire',65),('wire',66)];return m.events
 both(calibrated)
 groups.append('Alt1-through-Alt0-index54-context3-and-TEXT-routing')
 (OUT/'cpu-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((OUT/'METAKEYS.EXE').read_bytes()).hexdigest(),'cases':counts,'original_comparisons':original_count,'groups':groups,'fixtures':'ASPECT/program/resolver/UI/UART boundaries record arguments only; no program spawned. BIOS046c advances at actual tick-helper comparisons.','limitations':PROOF['limitations']},indent=2)+'\n')
 print('META keys:',len(groups),'groups,',counts,'cases,',original_count,'genuine-original comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');run(p.parse_args().original)
