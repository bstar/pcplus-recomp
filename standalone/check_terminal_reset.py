#!/usr/bin/env python3
"""Execute recovered reset with real dependencies; unrecovered services trap."""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_scroll import Scroll
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-reset'
class Dependency(Exception):pass
class Reset(Scroll):
 def __init__(self,original=False):
  DosImage.__init__(self,OUT/'RESET.EXE',OUT/'terminal_reset.map');self.original_mode=original;self.ports=[];self.calls=[]
  proof=json.loads((ROOT/'reconstruction/terminal_reset/provenance.json').read_text())
  aliases={name:int(at,16) for name,at in re.findall(r'^(\w+) equ reset_data_image\+0x([0-9a-f]+)$',(ROOT/'standalone/terminal_reset_host.asm').read_text(),re.M)}
  if original:
   sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
   image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(image).hexdigest()==proof['source_sha256'];self.uc=load_image(image);self.ds=0x1fb7;self.data_base=self.ds*16
   self.symbols={name:self.data_base+at for name,at in aliases.items()}
   for unit in proof['units']:
    source=(ROOT/unit['file']).read_text();name=re.search(r'^global (\w+)$',source,re.M)[1];self.symbols[name]=0x10000+unit['start']
   self.symbols['screen_set_cursor']=0x11bbe
   self.uc.mem_write(self.data_base,bytes(0xd600))
   host=(ROOT/'standalone/terminal_reset_host.asm').read_text().split('terminal_reset_test_initialize:',1)[1]
   for name,value in re.findall(r'^ mov word \[(\w+)\],(\w+)$',host,re.M):
    self.put(name,aliases[value] if value in aliases else int(value,0))
   self.uc.hook_add(UC_HOOK_CODE,self._stop)
  self.uc.hook_add(UC_HOOK_CODE,self.observe);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.hook_add(UC_HOOK_INSN,self.input,None,1,0,UC_X86_INS_IN);self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
  if not original:self.call('terminal_reset_test_initialize')
  self.original=[0x1e41+i%26 for i in range(2000)];self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original))
  self.uc.mem_write(0x485,b'\x10')
  self.aliases=aliases
  self.dependencies={0x10000+int(at,16):name for name,at in re.findall(r'^(\w+):\n mov ax,0x([0-9a-f]+)\n mov \[reset_unimplemented_service\]',(ROOT/'standalone/terminal_reset_host.asm').read_text(),re.M)}
 def observe(self,u,address,size,_):
  if self.original_mode and address in self.dependencies:raise Dependency(address-0x10000)
 def interrupt(self,u,n,_):
  if n==3:raise Dependency(self.get('reset_unimplemented_service'))
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==1:self.calls.append({'cursor_shape':u.reg_read(UC_X86_REG_CX)});return
  return Scroll.interrupt(self,u,n,None)
 def input(self,u,port,size,_):return 0x09
 def output(self,u,port,size,value,_):self.ports.append((port,value))
 def raw(self,address,width=2):
  name=next(name for name,at in self.aliases.items() if at==address);return self.get(name,width)
 def setraw(self,address,value,width=2):
  name=next(name for name,at in self.aliases.items() if at==address);self.put(name,value,width)
 def soft_snapshot(self):return self.cells(),self.rowcol(),self.get('attributes_current'),bytes(self.uc.mem_read(self.symbols['terminal_tab_stops'],30)),self.get('screen_attribute_row_bytes'),self.get('screen_viewport_enabled'),self.ports,self.calls

def run(compare=False):
 cases=[];comparisons=0
 def check(name,operation):operation();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def both(fn,snapshot):
  nonlocal comparisons
  models=[]
  for original in ([False,True] if compare else [False]):
   m=Reset(original);fn(m);models.append(snapshot(m))
  if compare:assert models[0]==models[1];comparisons+=1
 def soft():
  def execute(m):
   m.position(5,17);m.call('terminal_reset_native',[0],limit=1000000)
   assert m.cells()==[0x0720]*2000 and m.rowcol()==(0,0) and m.get('attributes_current')==7
   assert bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))==bytes(list(range(0,80,8))+[254]*20)
   assert m.get('screen_attribute_row_bytes')==80 and not m.get('screen_viewport_enabled')
  both(execute,lambda m:m.soft_snapshot())
 check('complete-soft-reset-stable-80column-hidden-status-real-clear-home-geometry-tabs',soft)
 flag_ranges={0xd122:(1,11),0x8fe8:(2,11),0x8ff6:(6,7),0x8ff8:(13,14),0x9004:(22,30),0xcd36:(25,28),0x9038:(22,29),0x900c:(22,32),0x9018:(31,32),0x9020:(15,17),0x9026:(18,19),0x9032:(20,21)}
 def profiles():
  for profile in list(range(35))+[65535]:
   def execute(m):
    m.put('csi_terminal_id',profile)
    try:m.call('terminal_reset_native',[1],limit=1000000)
    except Dependency as e:assert e.args==(0x0cd2,)
    else:raise AssertionError('Native mandatory KEY loader was silently skipped')
    for address,(lo,hi) in flag_ranges.items():assert m.raw(address)==int(lo<=profile<=hi),(profile,hex(address),m.raw(address))
    for address,want in [(0x903e,profile in(22,31)),(0x9048,profile==29),(0x904c,profile==30),(0x9056,profile==24),(0x9058,profile not in range(15,18) and profile not in range(20,33))]:assert m.raw(address)==int(want),(profile,hex(address),m.raw(address))
    assert m.cells()==[0x0720]*2000
   both(execute,lambda m:([m.raw(a) for a in list(flag_ranges)+[0x903e,0x9048,0x904c,0x9056,0x9058]],m.cells()))
 check('all-profile-derived-prefix-flags-and-honest-mandatory-KEY-dependency',profiles)
 def widths():
  for wide in (0,1):
   def execute(m):
    m.call('terminal_reset_width',[wide]);assert m.get('screen_last_column')==(131 if wide else 79) and m.get('screen_attribute_row_bytes')==(132 if wide else 80)
   both(execute,lambda m:(m.get('screen_last_column'),m.get('screen_attribute_row_bytes'),m.get('erase_cell_count'),m.get('screen_viewport_active')))
 check('actual-80-and132-width-state-helper',widths)
 def allocation():
  def execute(m):
   m.setraw(0x7a74,25)
   try:m.call('terminal_reset_geometry',[1,1],limit=1000000)
   except Dependency as e:assert e.args==(0x860f,)
   else:raise AssertionError('Far allocation silently fabricated')
  both(execute,lambda m:(m.get('screen_attribute_row_bytes'),m.get('screen_viewport_enabled')))
 check('geometry-wide-transition-exposes-real-far-allocation-boundary',allocation)
 def underline():
  for enable in (0,1):
   def execute(m):m.setraw(0x7a90,0x3d4);m.call('terminal_set_underline_scanline',[enable]);assert m.ports==[(0x3d4,20),(0x3d5,15 if enable else 31)]
   both(execute,lambda m:m.ports)
 check('actual-CRTC-underline-register-and-BDA-height-contract',underline)
 def special_soft():
  def execute(m):
   m.setraw(0x903e,1);m.position(5,17);m.call('terminal_reset_native',[0],limit=1000000)
   assert m.cells()==m.original and m.rowcol()==(5,17) and m.get('attributes_current')==0x1e
  both(execute,lambda m:m.soft_snapshot())
 check('native-special-zero-reset-preserves-screen-attribute-and-saved-cursor',special_soft)
 def shadow():
  def execute(m):
   m.put('screen_viewport_enabled',1);m.put('erase_shadow_segment',0x6000);m.put('erase_shadow_offset',0);m.put('reset_shadow_bytes',4000);m.uc.mem_write(0x60000,b'X'*4000)
   m.call('terminal_reset_clear_shadow');assert bytes(m.uc.mem_read(0x60000,4000))==b' \x07'*2000
  both(execute,lambda m:bytes(m.uc.mem_read(0x60000,4000)))
 check('actual-far-shadow-clear-uses-configured-normal-attribute',shadow)
 def script_status_pointer():
  def execute(m):
   m.put('reset_status_hidden',0);m.put('meta_script_active',1)
   label=m.symbols['terminal_reset_script_label']
   m.uc.mem_write(label,b'OWNED.ASX\0')
   try:m.call('terminal_reset_status_refresh',limit=1000000)
   except Dependency as e:assert e.args==(0xaa5c,)
   else:raise AssertionError('Status UART dependency was silently skipped')
   pointer=struct.unpack('<H',m.uc.mem_read(m.data_base+m.uc.reg_read(UC_X86_REG_BP)-2,2))[0]
   assert pointer==label-m.data_base,('Unrelocated script label',hex(pointer),hex(label-m.data_base))
   assert bytes(m.uc.mem_read(m.data_base+pointer,10))==b'OWNED.ASX\0'
  both(execute,lambda m:bytes(m.uc.mem_read(m.symbols['terminal_reset_script_label'],10)))
 check('status-script-label-pointer-relocates-before-explicit-UART-boundary',script_status_pointer)
 def cursor():
  for configured in (0,1):
   def execute(m):
    m.setraw(0x1d48,configured);m.call('terminal_reset_cursor_default');assert m.get('cursor_shape_start_scanline')==(6 if not configured else 0)
   both(execute,lambda m:(m.get('cursor_shape_start_scanline'),m.calls))
 check('native-default-cursor-shape-through-real-BIOS-helper',cursor)
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'RESET.EXE').read_bytes()).hexdigest(),'cases':cases,'genuine_original_comparisons':comparisons,'scope':'Full native soft-reset only for stable80-column geometry/status-hidden synthetic state. Nonzero profile prefix stops explicitly at original mandatory KEY loader; far allocation/UI/repair are not fake no-ops. Only video/CRTC hardware modeled.'}
 (OUT/('checks-original.json' if compare else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(len(cases),'groups',comparisons,'genuine comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args();run(a.original)
