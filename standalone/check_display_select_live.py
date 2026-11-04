#!/usr/bin/env python3
"""Execute banked selector/BIOS owner; BIOS effects modeled, no canonical UI commit."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_row_geometry_live import Geometry
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Selection(Geometry):
 def __init__(self,adapter='vga',vendor=False):self.vendor=vendor;self.vendor_calls=[];super().__init__(adapter)
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x10 and ax==0x6f00:
   if self.vendor:u.reg_write(UC_X86_REG_BX,0x5637)
   return
  if n==0x10 and ax==0x6f05:
   mode=u.reg_read(UC_X86_REG_BX);self.vendor_calls.append(mode);u.reg_write(UC_X86_REG_AX,mode&255)
   return self.interrupt(u,n,d)
  result=super().interrupt(u,n,d)
  if n==0x10 and ax>>8==0:self.uc.mem_write(0x463,struct.pack('<H',0x3b4 if self.mode==7 else 0x3d4))
  return result
 def select(self,selector,rows=50,mode=3,out=None,flags=0x202):
  if out is None:out=self.offset('terminal_modem_settings')
  u=self.uc;seg,off=self.entries['_native_display_select'];sp=self.offset('terminal_stack_top')-12
  u.mem_write(self.data_base+sp,struct.pack('<6H',self.return_offset,self.code_segment,selector,rows,mode,out))
  u.mem_write(self.data_base+sp-2000,b'GUARD!')
  for reg,value in ((UC_X86_REG_CS,self.base_segment+seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),
   (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,flags)):u.reg_write(reg,value)
  self.returned=False;u.emu_start(self.symbols['_native_display_select'],0,count=3000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
  for reg,value in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x6789)):assert u.reg_read(reg)==value
  assert bytes(u.mem_read(self.data_base+sp-2000,6))==b'GUARD!'
  return u.reg_read(UC_X86_REG_AX),struct.unpack('<12H',u.mem_read(self.data_base+out,24)) if out else None
 def canonical(self):
  return tuple(self.get(n) for n in ('csi_row_count','csi_last_row','ui_window_rows','ui_flow_video_base','ui_flow_suppressed','screen_cursor_row','screen_cursor_column'))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();mfest=json.loads((binary.parent/'manifest.json').read_text());assert mfest['experimental_display_preferences'] and sha(binary)==mfest['binary_sha256']
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map';out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print('PASS',name,n,flush=True)
 m=Selection();canonical=m.canonical()
 for selector,rows,mode,want_rows,want_selector,rc in [(1,50,0,25,1,0),(2,43,0,43,2,0),(0,50,3,43,0,0),(3,50,3,25,3,0),(4,50,3,50,4,0),(3,50,0,25,1,0),(4,50,0,25,1,0),(3,50,0x12,25,1,3)]:
  status,r=m.select(selector,rows,mode);assert status==rc and r[2]==want_rows and r[10:]==(selector,want_selector),(selector,status,r)
  assert m.canonical()==canonical and not m.tx
 done('physical-selector-chain-preserves-independent-canonical-state',8)
 count=0
 for adapter in ('vga','ega','cga'):
  for selector in (2,4):
   for rows in (0,25,28,43,50,0x12b,0xff32,0x8000,0xffff):
    m=Selection(adapter);status,r=m.select(selector,rows)
    want=25 if adapter=='cga' else ({28:28,43:43,50:50}.get(rows&255,25) if adapter=='vga' else (43 if rows&255==43 else 25))
    accepted=1 if adapter=='cga' and selector==4 else selector
    assert status==0 and r[2]==want and r[11]==accepted,(adapter,selector,rows,status,r);count+=1
 done('native-row-lowbyte-capabilities-and-mode-admission',count)
 count=0
 for selector in (3,4):
  for mode in (0,2,3,7,0x12,0x7f,0x80,0x7fff,0x8000,0xffff):
   m=Selection();status,r=m.select(selector,43,mode)
   eligible=0<mode<0x8000
   if not eligible:assert status==0 and r[11]==1 and r[9]==1 and r[2]==25
   elif mode in (2,3,7):assert status==0 and r[0]==mode and r[11]==selector and r[2]==(25 if selector==3 else 43)
   else:assert status==3 and r[0]==3 and r[2]==25 and r[9]==1 and r[11]==1
   count+=1
 done('signed-mode-admission-supported-text-and-verified-graphics-refusal-fallback',count)
 for rows in (28,43,50):
  m=Selection();m.font_refusals=1;status,r=m.select(2,rows);assert status==3 and r[2]==25 and r[11]==1 and r[9]==1
 done('refused-font-request-returns-verified-baseline',3)
 m=Selection();assert m.select(2,43)[0]==0;m.mode_refusals=2
 status,r=m.select(1);assert status==4 and r[2]==43 and r[11]==0xffff and r[9]==1
 done('unverified-baseline-recovery-remains-unusable',1)
 for refusals,want_status,want_mode in ((1,3,3),(2,4,2)):
  m=Selection();assert m.select(3,50,2)[0]==0;m.mode_refusals=refusals
  status,r=m.select(1);assert status==want_status and r[0]==want_mode and r[2]==25
  assert r[11]==(1 if want_status==3 else 0xffff)
 done('baseline-mode-is-verified-even-when-row-count-already-matches',2)
 m=Selection(vendor=True);status,r=m.select(3,50,0x12)
 assert m.vendor_calls==[0x12] and status==3 and r[0]==3 and r[11]==1
 done('actual-recovered-vendor-mode-branch-with-verified-fallback',1)
 count=0
 for selector,ptr,flags,want in [(5,None,0x202,1),(0xffff,None,0x202,1),(1,0,0x202,1),(1,0xfff0,0x202,1),(1,None,2,1),(1,None,0x602,1)]:
  m=Selection();before=m.canonical();hardware=list(m.hardware);status,r=m.select(selector,out=ptr,flags=flags)
  assert status==want and m.canonical()==before and m.hardware==hardware;count+=1
 done('invalid-selector-pointer-and-flags-refuse-before-BIOS-mutation',count)
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual C/ASM mode/geometry/font/capability chains execute, including recovered vendor branch. BIOS effects/refusal modeled. Raw destructive physical service only; no screen rollback, canonical/RIS/UI/bridge commit, normal key, online/BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
