#!/usr/bin/env python3
"""Linked recovered line instructions against BIOS model and optional real original."""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
from unicorn import UC_HOOK_INTR,UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
from check_scroll import Scroll,UnrecoveredService
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/line-edit'
class Lines(Scroll):
 def __init__(self,original=False):
  DosImage.__init__(self,OUT/'LINES.EXE',OUT/'line_edit.map')
  if original:
   sys.path.insert(0,str(ROOT/'reconstruction'));from check_ansi_freeze import load_image
   data=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();proof=json.loads((ROOT/'reconstruction/line_edit/provenance.json').read_text());assert hashlib.sha256(data).hexdigest()==proof['source_sha256']
   self.uc=load_image(data);self.ds=0x1fb7;self.data_base=self.ds*16;self.symbols={}
   for module in ('screen','erase','scroll','line_edit'):
    p=json.loads((ROOT/f'reconstruction/{module}/provenance.json').read_text())
    self.symbols.update({name:self.data_base+int(addr,16) for addr,name in p['state'].items()})
   self.symbols.update({'csi_insert_line':0x1d668,'csi_delete_line':0x1d73c,'screen_set_cursor':0x11bbe})
   for name,value in re.findall(r'^state (\w+),(\d+)$',(ROOT/'standalone/line_edit_host.asm').read_text(),re.M):
    if name in self.symbols:self.put(name,int(value))
   self.symbols['erase_attribute_flags']=self.data_base+0x5000;self.symbols['erase_attribute_values']=self.data_base+0x6000
   self.put('screen_attributes_base',0x5000);self.put('erase_attribute_values_base',0x6000)
   self.put('erase_shadow_offset',0x7000);self.put('erase_shadow_segment',self.ds)
   self.uc.mem_write(self.symbols['erase_attribute_flags'],bytes(4096));self.uc.mem_write(self.symbols['erase_attribute_values'],bytes([7])*4096)
   self.uc.hook_add(UC_HOOK_CODE,self._stop)
  self.calls=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.original=[((i//80)%7+1)*256+(33+i%80) for i in range(2000)]
  self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original))
 def plane(self,name):return bytes(self.uc.mem_read(self.symbols[name],2080))

def run(compare=False):
 groups=[];comparisons=0
 for name,entry,delta in [('insert','csi_insert_line',-1),('delete','csi_delete_line',1)]:
  for top,bottom,row,protected,plane in [(0,24,5,0,0),(3,10,5,0,0),(0,24,24,0,0),(3,10,10,0,0),(0,24,5,1,0),(0,24,5,0,1)]:
   models=[]
   for original in ([False,True] if compare else [False]):
    c=Lines(original);c.put('screen_first_row',top);c.put('screen_last_row',bottom);c.put('csi_last_row',bottom);c.put('screen_attribute_checks',protected);c.position(row,17)
    if plane:
     c.put('screen_cursor_wrap',1);c.uc.mem_write(c.symbols['erase_attribute_flags'],bytes((i%0x40) for i in range(2080)));c.uc.mem_write(c.symbols['erase_attribute_values'],bytes(0x20+i%0x40 for i in range(2080)))
    before=c.cells();c.call(entry)
    if protected:assert c.cells()==before and c.rowcol()==(row,17) and not c.calls
    else:
     # Original one-line helper always homes column0 and uses cursor..bottom.
     assert c.rowcol()==(row,0)
     assert c.cells()[:row*80]==before[:row*80] and c.cells()[(bottom+1)*80:]==before[(bottom+1)*80:]
     if not plane:assert c.cells()==c.expected_scroll(row,bottom,delta)
    assert c.uc.reg_read(UC_X86_REG_BP)==0xbabe and c.uc.reg_read(UC_X86_REG_SI)==0x1234 and c.uc.reg_read(UC_X86_REG_DI)==0x5678
    models.append(c)
   if compare:
    a,b=models;assert a.cells()==b.cells() and a.calls==b.calls and a.rowcol()==b.rowcol()
    if plane:
     for p in ['erase_attribute_flags','erase_attribute_values']:assert a.plane(p)==b.plane(p),(name,p)
    comparisons+=1
  groups.append(name+'-normal-margins-bottom-protection-attributeplanes-ABI')
 # Actual original wait instructions linked to declared configurable fixtures.
 c=Lines();c.put('wait_uart_value',14);c.call('csi_wait_control_n')
 c=Lines();c.put('wait_uart_value',0xffff);c.put('wait_key_value',27);c.call('csi_wait_control_n');assert c.get('wait_key_value')==0
 c=Lines();c.put('wait_uart_value',0xffff);c.put('wait_key_value',ord('x'))
 try:c.call('csi_wait_control_n',limit=300)
 except AssertionError as error:assert 'failed to return' in str(error)
 else:raise AssertionError('Original indefinite wait unexpectedly gained a timeout')
 groups.append('wait-control-N-local-Escape-other-key-consumption-and-original-no-timeout')
 # The complicated repair branch is intentionally an explicit dependency.
 c=Lines();c.position(5,0);c.put('screen_cursor_wrap',1);c.uc.mem_write(c.symbols['erase_attribute_flags']+5*80,b'\x80')
 try:c.call('csi_delete_line')
 except UnrecoveredService as e:assert e.args==(0x2d98,)
 else:raise AssertionError('Missing original attribute repair was silently skipped')
 groups.append('nontrivial-attribute-repair-remains-explicit-fail-fast')
 (OUT/'cpu-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256((OUT/'LINES.EXE').read_bytes()).hexdigest(),'groups':groups,'original_comparisons':comparisons,'limitations':['INT10 video oracle and explicit UART/keyboard wait fixtures; no physical serial hardware.','Helpers edit one line; count normalization belongs to existing CSI dispatcher.','No unsafe-state guard added to exact assembly; fixed23-row attribute copy preserved.']},indent=2)+'\n')
 print('Line editing:',len(groups),'groups,',comparisons,'genuine original comparisons passed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');run(p.parse_args().original)
