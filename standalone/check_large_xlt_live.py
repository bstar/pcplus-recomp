#!/usr/bin/env python3
"""Execute large-screen XLT editor/reload owners; BIOS/UART/DOS boundaries modeled.
No actual editor child, BBS/SIP or physical acceptance in this checker.
"""
import argparse,hashlib,json
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_program_display_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from program_display_model import Program
 from check_translation_edit_live import Editor
 from check_live_translation import Translation,IDENTITY,CURRENT
 from check_recording_rx_live import ordinary
 class Large(Program,Editor):
  def interrupt(self,u,n,d):
   ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;h=u.reg_read(UC_X86_REG_BX)
   if n==0x21 and (ax==0x6000 or ax==0x3d00 and self.string(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX)).endswith(b'.XLT') or ah in (0x3f,0x3e) and h in self.xlt_handles):
    return Translation.interrupt(self,u,n,d)
   return super().interrupt(u,n,d)
  def run(self,rows,hidden,source,action='edit',choice=ord('Y'),fault=None):
   self.bind(source,fallback=source==b'D:\\ENV\\PCPLUS.XLT',explicit=source.endswith(b'CUSTOM.XLT'))
   self.install_program_name();self.setup(rows,hidden);self.prompt_key_sent=True
   self.edited_source=source;self.edited=changed
   if action=='reload':self.xlt_files[source]=changed
   if fault=='exec':self.exec_error=2
   if fault=='short':
    if action=='edit':self.edited=bytes(255)
    else:self.xlt_files[source]=bytes(255)
   if fault=='close':self.xlt_fault='close'
   before=self.full()
   self.keys.extend([0x1100 if action=='edit' else 0x7000,choice]);self.poll()
   assert self.get('terminal_program_pending') and self.get('terminal_program_kind')==(3 if action=='edit' else 2),(rows,hidden,source,action,list(self.keys),{n:self.get(n) for n in ['terminal_translation_edit_status','terminal_translation_reload_status','terminal_translation_mode','terminal_translation_enabled','uart_rx_mask','terminal_program_status','terminal_program_pending','terminal_program_kind']})
   self.safe();self.verify(rows)
   assert not self.keys and not self.get('terminal_deferred_count')
   after=self.full()
   for name in ('words','bytes','defaults','planes','ui','hardware'):assert after[name]==before[name],(rows,hidden,source,action,fault,name)
   expected=IDENTITY if fault or choice!=ord('Y') else changed
   assert self.table()==expected
   assert self.get('terminal_translation_mode')==self.get('terminal_translation_enabled')==1 and self.get('uart_rx_mask')==255
   status=self.get('terminal_translation_edit_status' if action=='edit' else 'terminal_translation_reload_status')
   assert status==(7 if fault=='exec' else 5 if fault else 2 if choice==ord('Y') else 3),status
   assert not self.get('_program_display_ready')
   # Run actual input translation + parser after restoration. ESC remains raw.
   ordinary(self,b'\x1b[1;1HL');self.drain()
   assert bytes(self.uc.mem_read(0xb8000,2))==bytes([expected[76],7])
   # Keyboard transmission remains independent of the receive-only table.
   sent=len(self.tx);self.keys.append(ord('L'));self.poll();self.drain();assert bytes(self.tx[sent:])==b'L'
 changed=bytearray(range(256));changed[76]=88;changed=bytes(changed)
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 count=0
 for rows in [25,28,43,50]:
  for hidden in [0,1]:
   for action in ['edit','reload']:
    for source in [CURRENT,b'D:\\ENV\\PCPLUS.XLT',b'D:\\WORK\\CUSTOM.XLT']:
     for choice in [ord('Y'),ord('N')]:
      Large().run(rows,hidden,source,action,choice);count+=1
 done('all-heights-status-states-default-fallback-explicit-editor-reload-accept-decline-render-and-raw-TX',count)
 count=0
 for rows in [25,28,43,50]:
  for action,fault in [('edit','exec'),('edit','short'),('edit','close'),('reload','short'),('reload','close')]:
   Large().run(rows,0,CURRENT,action,32,fault);count+=1
 done('failed-EXEC-and-invalid-read-close-retain-table-and-full-parent-at-each-height',count)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_large_xlt_live.py','standalone/program_display_model.py','standalone/check_translation_edit_live.py','standalone/check_translation_reload_live.py','standalone/check_live_translation.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
