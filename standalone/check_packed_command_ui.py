#!/usr/bin/env python3
"""Compare actual linked browser draw/help/search frames before and after text packing."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_path_session import ROOT,sha

class Menu:
 def __init__(self,binary):
  self.m=DosImage(binary,binary.with_name('terminal.map'));self.u=self.m.uc
  listing=binary.with_name('terminal.map').read_text()
  matches=re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_command_menu_event\s*$',listing,re.M|re.I)
  assert len(matches)==1
  seg,off=(int(v,16) for v in matches[0]);self.target=(off,seg+self.m.base_segment)
  self.u.mem_write(0xe0000,b'\x9a'+struct.pack('<HH',*self.target)+b'\xf4')
  self.returned=False
  def stop(u,address,size,unused):
   if address==0xe0005:self.returned=True;u.emu_stop()
  self.u.hook_add(UC_HOOK_CODE,stop)
  def forbidden(*args):raise AssertionError('UI comparison reached an unexpected interrupt')
  self.u.hook_add(UC_HOOK_INTR,forbidden)
  self.u.mem_write(0xb8000,b'\x20\x07'*2000)
 def event(self,event,key=0):
  sp=self.m.offset('terminal_stack_top')-64
  self.u.mem_write(self.m.data_base+sp,struct.pack('<4H',event,key,0,0xb800))
  for r,v in [(UC_X86_REG_CS,0xe000),(UC_X86_REG_IP,0),(UC_X86_REG_DS,self.m.ds),
              (UC_X86_REG_SS,self.m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  self.returned=False;self.u.emu_start(0xe0000,0,count=3000000)
  assert self.returned and self.u.reg_read(UC_X86_REG_SP)==sp
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==self.m.ds
  return (self.u.reg_read(UC_X86_REG_AX),bytes(self.u.mem_read(0xb8000,4000)),
          self.m.get('_command_menu_active'),self.m.get('_command_menu_action'))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['plain','packed','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();plain=a.plain.resolve();packed=a.packed.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 for binary in [plain,packed]:
  m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 assert json.loads(plain.with_name('manifest.json').read_text())['packed_command_ui']['pairs']==0
 assert json.loads(packed.with_name('manifest.json').read_text())['experimental_packed_command_ui']
 left,right=Menu(plain),Menu(packed);rows=[]
 def compare(label,event,key=0):
  before=left.event(event,key);after=right.event(event,key)
  assert before==after,label
  rows.append(dict(step=label,frame_sha256=hashlib.sha256(after[1]).hexdigest()))
 compare('browser-open',0,ord('`'))
 for word in [b'File',b'Connection',b'View',b'Setup',b'Help']:
  assert word in bytes(right.u.mem_read(0xb8000+320,160))[::2]
 for group in range(5):
  for index in range(18):compare(f'group-{group}-item-{index}',1,0x5000)
  compare(f'group-{group}-help',1,0x3b00)
  for index in range(9):compare(f'group-{group}-help-next-{index}',1,0x5000)
  compare(f'group-{group}-help-return',1,27)
  compare(f'group-{group}-tab',1,9)
 for query in ['editor','Alt-A','Enter parameters','call log','interval','A'*31,' ','return to',' DOS ','zzzzzzzz']:
  compare('reset',0,ord('`'));compare('query-open-'+query,1,ord('/'))
  for ch in query:compare('query-byte-'+query,1,ord(ch))
  compare('query-search-'+query,1,13);compare('query-help-return-'+query,1,27)
 for n in range(39):
  compare('reference-open',0,0x2c00)
  for _ in range(n):compare('reference-down',1,0x5000)
  compare('reference-help',1,0x3b00)
  compare('reference-close',1,27)
 result=dict(passed=True,plain_sha256=sha(plain),binary_sha256=sha(packed),identical_frames=len(rows),
             cases=rows,sources={n:sha(ROOT/n) for n in ['standalone/check_packed_command_ui.py','standalone/dos_image.py']},
             scope=__doc__+' Actual linked far-cdecl menu entry; complete4000-byte frames,return values and action/active flags. No application callbacks replaced. Interrupts reject. Full terminal/DOS/hardware acceptance is separate.')
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(rows),'exact UI frames and return/owner states')
if __name__=='__main__':main()
