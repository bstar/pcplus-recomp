#!/usr/bin/env python3
"""Run actual linked report handlers with maintained decimal and captured output."""
import hashlib,json,random
from pathlib import Path
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class Reports(DosImage):
 def __init__(self,**state):
  super().__init__(ROOT/'build/reports/REPORTS.EXE',ROOT/'build/reports/reports.map')
  for name,value in state.items():self.put(name,value&0xffff)
 def reply(self,name='csi_device_status'):
  self.put('reports_output_length',0)
  self.call(name)
  return bytes(self.uc.mem_read(self.symbols['reports_output_buffer'],self.get('reports_output_length')))
 def decimal(self,value):
  offset=self.offset('reports_decimal_test_buffer')
  result=self.call('csi_report_decimal',[value&0xffff,offset,10])
  assert result==offset
  return bytes(self.uc.mem_read(self.symbols['reports_decimal_test_buffer'],7)).split(b'\0')[0]
def main():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed')
 def ordinary():
  r=Reports()
  for query,want in [(5,b'\x1b[0n'),(6,b'\x1b[10;20R'),(15,b'\x1b[?13n'),(0,b''),(7,b'')]:
   r.put('ansi_parameters',query);assert r.reply()==want,(query,r.reply())
  r.put('csi_printer_ready',1);assert r.reply()==b''
  r.put('ansi_parameters',15);assert r.reply()==b'\x1b[?10n'
 check('ordinary-status-cursor-printer-and-unknown-queries',ordinary)
 def origin_private():
  for private in (0,1):
   for prefix in (0,1):
    r=Reports(ansi_parameters=6,screen_cursor_row=20,screen_cursor_column=79,csi_origin_row=10,ansi_private=private,csi_report_private_prefix=prefix)
    assert r.reply()==b'\x1b['+(b'0;' if private and prefix else b'')+b'11;80R'
 check('origin-relative-coordinates-and-private-prefix-gating',origin_private)
 def signed():
  r=Reports();rng=random.Random(201)
  for value in [0,1,9,10,99,100,32767,32768,65535]+[rng.randrange(65536) for _ in range(512)]:
   signed=value if value<32768 else value-65536
   assert r.decimal(value)==str(signed).encode(),value
  r=Reports(ansi_parameters=6,screen_cursor_row=65535,screen_cursor_column=32767,csi_origin_row=1)
  assert r.reply()==b'\x1b[-1;-32768R'
 check('maintained-signed-decimal-bounds-and-coordinate-wrap',signed)
 def attributes():
  for index,payload in [(2,b'1;2'),(3,b'6'),(4,b'62;2'),(5,b'63;2'),(6,b'1;2'),(7,b'1;2'),(8,b'1;0'),(9,b'7;5;1'),(10,b'1;2'),(11,b'62;2')]:
   r=Reports(csi_terminal_id=index);assert r.reply('csi_primary_attributes')==b'\x1b[?'+payload+b'c',index
 check('all-supported-original-device-attribute-profiles',attributes)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/reports/REPORTS.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked report instructions, maintained decimal, captured bytes; no UART or rendered terminal.'}
 (ROOT/'build/reports/cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
