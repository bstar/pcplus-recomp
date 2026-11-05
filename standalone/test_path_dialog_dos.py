#!/usr/bin/env python3
"""Actual DOS8086 Alt-F7, serviced UART, VGA dialog and startup restoration."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=harness.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--case',choices=('cancel','empty','relative','cross','missing','browser','reference','editing','serviced'))
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert not out.exists() and out.is_relative_to(ROOT/'build')
 manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert manifest['binary_sha256']==sha(binary) and manifest['experimental_path_control']
 out.mkdir(parents=True);package=out/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 settings=bytearray(prm(port=3,baud=5))
 for at,val in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)):
  struct.pack_into('<H',settings,at,val)
 scenarios=[
  ('cancel',1,'a-f7 p900 escape',b'D:\\'),
  ('empty',1,'a-f7 p900 enter',b'D:\\'),
  ('relative',2,'a-f7 p450 o t h e r enter p600 a-f7 p900 escape',b'D:\\OTHER'),
  ('cross',4,'a-f7 p450 c : \\ enter p600 a-f7 p900 escape',b'C:\\'),
  ('missing',3,'a-f7 p450 m i s s i n g enter p900 o t h e r enter',b'D:\\'),
  ('browser',2,'` p500 g p450 o t h e r enter p600 a-f7 p900 escape',b'D:\\OTHER'),
  ('reference',2,'a-z p500 a-f7 p450 o t h e r enter p600 a-f7 p900 escape',b'D:\\OTHER'),
  ('editing',2,'a-f7 p450 o t h e x left del r home right end enter p600 a-f7 p900 escape',b'D:\\OTHER'),
  ('serviced',5,'a-f7 p6000 escape',b'D:\\')]
 cases=[];harness.BINARY=package/'TERMINAL.EXE'
 for name,kind,keys,header in scenarios:
  if a.case and name!=a.case:continue
  observer=out/(name+'.COM')
  subprocess.run(['nasm','-fbin','-DWATCH_KIND='+str(kind),str(ROOT/'standalone/path_dialog_watch.asm'),'-o',str(observer)],check=True)
  case=out.name+'-'+name;drive=ROOT/'build/connection-dos'/case;assert not drive.exists()
  files={'PATHOBS.COM':observer.read_bytes(),'OTHER/KEEP.TXT':b'unchanged directory fixture\r\n'}
  base=harness.run(case,'success','p900 enter p3500 '+keys+' p600 r e a d y enter p1000 a-x',
   prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',
   files=files,observer='PATHOBS',timeout=30,
   online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-PATH-DIALOG\x1b[6n'),),
   online_updates=((5.0,b'\x1b[2;1HUART-WHILE-OPEN\x1b[6n'),) if name=='serviced' else ())
  raw=(drive/'PATHVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
  frame=raw[6:4006];wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
  chars=lambda row,col,n:frame[(row*80+col)*2:(row*80+col+n)*2:2]
  checks=dict(base['checks'])
  checks.update(observer_captured_and_restored=magic==0x5044 and flags==3 and ticks>2,
   original_popup_geometry=all(frame[(r*80+c)*2:(r*80+c)*2+2]==bytes((glyph,3)) for r,c,glyph in ((5,2,201),(5,77,187),(9,2,200),(9,77,188))),
   original_header=chars(5,5,14)==b' CURRENT DIR: ' and chars(5,19,len(header))==header,
   original_prompt=chars(7,4,9)==b'NEW PATH:',
   original_field_attributes=frame[(7*80+14)*2+1:(7*80+76)*2:2]==bytes([13])*62,
   startup_default_drive_restored=raw[4006]==3,
   startup_CWD_restored=raw[4007:].split(b'\0',1)[0]==b'',
   post_dialog_keyboard_reached_UART=wire.count(b'ready\r')==1,
   post_dialog_query_replied=b'\x1b[3;18R' in wire,
   post_dialog_input_rendered=screen[320:354:2]==b'AFTER-PATH-DIALOG')
  if name=='missing':checks['failed_change_keeps_dialog_open']=chars(8,4,14)==b'Path not found'
  if name=='serviced':
   checks['incoming_UART_rendered_with_popup_visible']=chars(1,0,15)==b'UART-WHILE-OPEN'
   checks['query_answered_while_popup_open']=b'\x1b[2;16R' in wire
  result=dict(case=name,passed=all(checks.values()),checks=checks,observed_header=chars(5,19,40).decode('cp437'),result=str(drive/'result.json'))
  cases.append(result);(out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  print(name,{k:v for k,v in checks.items() if not v},flush=True);assert result['passed'],result
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,
  sources={n:sha(ROOT/n) for n in ('standalone/test_path_dialog_dos.py','standalone/path_dialog_watch.asm','standalone/test_connection_dos.py')},
  scope=__doc__+' Synthetic serial modem, actual DOSBox-X8086 COM3/IRQ5; passive ISR observer only. No physical modem acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
