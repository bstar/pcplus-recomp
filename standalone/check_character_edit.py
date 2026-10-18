#!/usr/bin/env python3
"""Actual linked character editing, hardware oracle and opt-in original comparison."""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_scroll import Scroll,UnrecoveredService
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/character-edit'
class Characters(Scroll):
 def __init__(self,original=False):
  DosImage.__init__(self,OUT/'CHAREDIT.EXE',OUT/'character_edit.map');self.original_mode=original
  if original:
   sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
   data=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(data).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
   self.uc=load_image(data);self.ds=0x1fb7;self.data_base=self.ds*16;self.symbols={}
   for module in ('screen','erase','scroll','text','character_edit'):
    proof=json.loads((ROOT/f'reconstruction/{module}/provenance.json').read_text());self.symbols.update({name:self.data_base+int(addr,16) for addr,name in proof['state'].items()})
   self.symbols.update({'csi_insert_character':0x1d270,'csi_delete_character':0x1d440,'terminal_set_tab':0x1dac6,'character_cga_restore':0x177ae,'character_cga_disable':0x177be,'screen_set_cursor':0x11bbe})
   for name,value in re.findall(r'^state (\w+),(0x[0-9a-f]+|[0-9]+)$',(ROOT/'standalone/character_edit_host.asm').read_text(),re.M):
    if name in self.symbols:self.put(name,int(value,0))
   self.symbols['erase_attribute_flags']=self.data_base+0x5000;self.symbols['erase_attribute_values']=self.data_base+0x6000
   self.put('screen_attributes_base',0x5000);self.put('erase_attribute_values_base',0x6000)
   self.uc.hook_add(UC_HOOK_CODE,self._stop)
  self.calls=[];self.ports=[];self.reads=0
  self.uc.mem_write(self.symbols['screen_line_flags'],bytes(128))
  self.uc.mem_write(self.symbols['erase_attribute_flags'],bytes(4096));self.uc.mem_write(self.symbols['erase_attribute_values'],bytes([7])*4096)
  self.uc.mem_write(self.symbols['terminal_tab_stops'],bytes([254])*30)
  self.put('erase_shadow_segment',0x6000);self.put('erase_shadow_offset',0)
  self.uc.mem_write(0x60000,bytes(8192))
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.observe)
  self.uc.hook_add(UC_HOOK_INSN,self.input,None,1,0,UC_X86_INS_IN);self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
  self.original=[((i//80)%7+1)*256+(33+i%80) for i in range(2000)]
  self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original))
 def observe(self,u,address,size,_):
  if self.original_mode and address==0x12d98:raise UnrecoveredService(0x2d98)
 def input(self,u,port,size,_):self.reads+=1;assert port==0x3da;return 8+(self.reads%2)
 def output(self,u,port,size,value,_):self.ports.append((port,value))
 def flags(self):return bytes(self.uc.mem_read(self.symbols['erase_attribute_flags'],2080))
 def values(self):return bytes(self.uc.mem_read(self.symbols['erase_attribute_values'],2080))
 def shadow(self):return bytes(self.uc.mem_read(0x60000,8192))
 def snapshot(self):return self.cells(),self.flags(),self.values(),self.shadow(),self.rowcol(),self.get('csi_wrap_pending'),self.ports

def run(compare=False):
 groups=[];comparisons=0;cases=0
 def check(name,fixture,operation,verify):
  nonlocal comparisons,cases
  models=[]
  for original in ([False,True] if compare else [False]):
   m=Characters(original);fixture(m);before=m.snapshot();m.call(operation);verify(m,before)
   for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert m.uc.reg_read(reg)==want,(name,reg)
   models.append(m)
  if compare:assert models[0].snapshot()==models[1].snapshot(),name;comparisons+=1
  cases+=1
 def normal(row,col,width=1,insert=True):
  def setup(m):m.position(row,col);m.put('csi_wrap_pending',1);m.uc.mem_write(m.symbols['screen_line_flags']+row,bytes([0x40 if width==2 else 0]))
  def verify(m,before):
   cells=before[0][:];start=row*80+col;end=(row+1)*80
   if insert:cells[start:end]=[before[0][start]&0xff00|32]*width+before[0][start:end-width]
   else:cells[start:end]=before[0][start+width:end]+[0x0720]*width
   assert m.cells()==cells and m.rowcol()==(row,col)
   assert m.get('csi_wrap_pending')==(1 if insert else 0)
  return setup,verify
 for insert,entry in [(True,'csi_insert_character'),(False,'csi_delete_character')]:
  for row in (0,5,24):
   for col in (0,17,79):
    setup,verify=normal(row,col,1,insert);check(f'normal-{insert}-{row}-{col}',setup,entry,verify)
  for col in (0,16,78):
   setup,verify=normal(5,col,2,insert);check(f'double-{insert}-{col}',setup,entry,verify)
 groups.append('normal-border-cells-doublewidth-cursor-and-wrap-state')
 for insert,entry in [(True,'csi_insert_character'),(False,'csi_delete_character')]:
  for boundary in (12,20):
   def setup(m):
    m.position(5,12);m.put('screen_attribute_checks',1);m.uc.mem_write(m.symbols['erase_attribute_flags']+5*80+boundary,b'\x80')
   def verify(m,before):
    cells=before[0][:];start=5*80+12;end=5*80+boundary
    if boundary>12:
     if insert:cells[start:end]=[cells[start]&0xff00|32]+before[0][start:end-1]
     else:cells[start:end]=before[0][start+1:end]+[0x0720]
    assert m.cells()==cells and m.flags()==before[1]
   check(f'protected-{insert}-{boundary}',setup,entry,verify)
 groups.append('protected-current-cell-and-neighbor-stop-preservation')
 for insert,entry in [(True,'csi_insert_character'),(False,'csi_delete_character')]:
  def setup(m):
   m.position(5,12);m.put('screen_cursor_wrap',1)
   m.uc.mem_write(m.symbols['erase_attribute_flags'],bytes(i%0x40 for i in range(2080)));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(0x20+i%0x40 for i in range(2080)))
  def verify(m,before):
   start=5*80+12;end=6*80;flags=bytearray(before[1]);values=bytearray(before[2])
   if insert:
    flags[start+1:end]=before[1][start:end-1];values[start+1:end]=before[2][start:end-1];flags[start]&=254
   else:
    flags[start:end-1]=before[1][start+1:end];values[start:end-1]=before[2][start+1:end];flags[end-1]&=254
   assert m.flags()==flags and m.values()==values
  check('attribute-planes-'+entry,setup,entry,verify)
  def double_setup(m):setup(m);m.uc.mem_write(m.symbols['screen_line_flags']+5,b'\x40')
  check('double-attribute-planes-'+entry,double_setup,entry,verify)
 groups.append('actual-900c-attribute-and-value-plane-shifts')
 for insert,entry in [(True,'csi_insert_character'),(False,'csi_delete_character')]:
  def setup(m):
   m.position(0,12);m.put('screen_last_column',131);m.put('screen_attribute_row_bytes',132);m.put('screen_viewport_active',1)
   m.uc.mem_write(0x60000,struct.pack('<4096H',*(0x1e00+(i%94)+33 for i in range(4096))))
  def verify(m,before):
   old=before[0][:80]+list(struct.unpack('<52H',before[3][160:264]));expected=old[:]
   if insert:expected[12:]=[old[12]&0xff00|32]+old[12:-1]
   else:expected[12:]=old[13:]+[0x0720]
   assert m.cells()[:80]==expected[:80] and m.cells()[80:]==before[0][80:]
   assert list(struct.unpack('<52H',m.shadow()[160:264]))==expected[80:]
  check('viewport-'+entry,setup,entry,verify)
 groups.append('132-column-right-shadow-and-visible-cell-transfer')
 for entry in ('csi_insert_character','csi_delete_character'):
  check('CGA-'+entry,lambda m:(m.position(5,12),m.put('text_cga_status_port',0x3da)),entry,lambda m,b: m.ports==[(0x3d8,0x25),(0x3d8,0x2d)] or (_ for _ in ()).throw(AssertionError(m.ports)))
 groups.append('actual-CGA-disable-status-wait-and-restore-port-paths')
 for table,col,expected in [([8,16,24]+[254]*27,8,[8,16,24]+[254]*27),([8,16,24]+[254]*27,12,[8,12,24]+[254]*27),([254]*30,5,[5]+[254]*29),(list(range(30)),40,list(range(30))),(list(range(29))+[254],40,list(range(28))+[40,254]),([254]*30,0x105,[5]+[254]*29),([254]*30,0,[0]+[254]*29)]:
  check('set-tab-'+str(col),lambda m:(m.put('screen_cursor_column',col),m.uc.mem_write(m.symbols['terminal_tab_stops'],bytes(table))),'terminal_set_tab',lambda m,b: bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))==bytes(expected) or (_ for _ in ()).throw(AssertionError('tab')))
 groups.append('set-tab-existing-replace-next-sentinel-and-full-table')
 m=Characters();m.position(5,12);m.put('screen_cursor_wrap',1);m.uc.mem_write(m.symbols['erase_attribute_flags']+5*80+12,b'\x80')
 try:m.call('csi_delete_character')
 except UnrecoveredService as e:assert e.args==(0x2d98,)
 else:raise AssertionError('Complex attribute repair was hidden')
 groups.append('complex-current-attribute-repair-explicit-trap')
 result={'passed':True,'binary_sha256':hashlib.sha256((OUT/'CHAREDIT.EXE').read_bytes()).hexdigest(),'groups':groups,'cases':cases,'genuine_original_comparisons':comparisons,'scope':'Actual character-edit instructions plus real screen/erase/text dependencies. Only BIOS/CGA hardware modeled; protected attribute repair explicitly trapped. Original comparison opt-in; no private configuration or original needed by source-only build.'}
 (OUT/('checks-original.json' if compare else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(len(groups),'groups',cases,'cases',comparisons,'genuine comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true');a=p.parse_args();run(a.original)
