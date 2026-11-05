#!/usr/bin/env python3
"""Actual DOS Alt-F/menu listing, paging, error and serviced return workflows."""
import argparse,datetime,json,os,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import sha
ROOT=harness.ROOT

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case');a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_file_directory'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);harness.BINARY=binary
 settings=bytearray(prm(port=3,baud=5))
 for at,val in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,val)
 recipes=[('cancel',1,'a-f p900 escape'),('empty',6,'a-f p400 enter p1600 escape'),
  ('page',2,'a-f p400 f i l e s \\ * . t x t enter p1600 escape'),
  ('next',3,'a-f p400 f i l e s \\ * . t x t enter p1000 space p1400 escape'),
  ('missing',4,'a-f p400 n o f i l e . x enter p1400 space'),
  ('reference',2,'a-z p400 a-f p400 f i l e s \\ * . t x t enter p1600 escape'),
  ('browser',2,'` p400 i p400 f i l e s \\ * . t x t enter p1600 escape'),
  ('serviced',5,'a-f p400 f i l e s \\ * . t x t enter p6000 escape'),
  ('loading-cancel',1,'a-f p900 enter escape p800')]
 cases=[]
 for name,kind,keys in recipes:
  if a.case and a.case!=name:continue
  observer=out/(name+'.COM');subprocess.run(['nasm','-fbin','-DWATCH_KIND='+str(kind),str(ROOT/'standalone/file_dialog_watch.asm'),'-o',str(observer)],check=True)
  case=out.name+'-'+name;drive=ROOT/'build/connection-dos'/case;assert not drive.exists()
  files={'FILEOBS.COM':observer.read_bytes(),**{'FILES/F%02d.TXT'%i:b'X'*(i+1) for i in range(22)}}
  def stamp(folder):
   t=datetime.datetime(1993,7,9,14,32,10).timestamp()
   for f in (folder/'FILES').iterdir():os.utime(f,(t,t))
  base=harness.run(case,'success','p900 enter p3500 '+keys+' p600 r e a d y enter p1000 a-x',
   prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',
   files=files,observer='FILEOBS',timeout=30,dial_action=stamp,
   online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-FILE-DIALOG\x1b[6n'),),
   online_updates=((5.0,b'\x1b[23;1HUART-WHILE-OPEN\x1b[6n'),) if name=='serviced' else ())
  raw=(drive/'FILEVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw);frame=raw[6:4006]
  wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
  chars=lambda r,c,n:frame[(r*80+c)*2:(r*80+c+n)*2:2]
  checks={**base['checks'],'passive_observer_and_restore':magic==0x4644 and flags==3 and ticks>2,
   'startup_drive_and_directory':raw[4006]==3 and raw[4007:].split(b'\0',1)[0]==b'',
   'keyboard_after_dialog':wire.count(b'ready\r')==1,'post_dialog_query':b'\x1b[3;18R' in wire,
   'post_dialog_display':screen[320:354:2]==b'AFTER-FILE-DIALOG'}
  if kind==1:checks.update(prompt_geometry=frame[(10*80+5)*2:(10*80+5)*2+2]==bytes([201,11]),prompt_label=b'Enter FILE SPEC:' in frame[::2],live_background=chars(0,0,15)==b'FIRST BYTE SAFE')
  elif kind==4:checks['not_found']=chars(10,32,17)==b'File(s) not found'
  else:
   checks['heading']=chars(2,22,36)==b'FILE NAME       SIZE    DATE    TIME'
   checks['listing_geometry']=all(frame[(r*80+c)*2:(r*80+c)*2+2]==bytes([g,7]) for r,c,g in [(1,20,201),(1,60,187),(21,20,200),(21,60,188)])
   if name!='empty':checks['first_record']=chars(4,22,7)==(b'F15.TXT' if kind==3 else b'F00.TXT')
   if kind==2:checks['more']=chars(20,37,8)==b'- MORE -'
   if kind==3:checks.update(last_record=chars(10,22,7)==b'F21.TXT',partial_page_no_more=chars(20,37,8)==b' '*8,cleared_unused_rows=chars(11,22,38)==b' '*38)
   if name=='serviced':checks.update(UART_during_dialog=chars(22,0,15)==b'UART-WHILE-OPEN',query_while_open=b'\x1b[23;16R' in wire)
  result=dict(case=name,passed=all(checks.values()),checks=checks)
  cases.append(result);(out/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  assert result['passed'],result
 assert cases
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/test_file_dialog_dos.py','standalone/file_dialog_watch.asm','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/directory_fixtures.py']
 r=dict(passed=True,cases=cases,binary_sha256=sha(binary),sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__+' Actual DOS8086 COM3/IRQ5 with synthetic serial peer and owned files. Passive VGA reads; real directory calls, ordinary keyboard, BIOS frames/query responses and final UART/PIC/vector restoration. No physical/SIP/DSP or full viewer parity.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(cases),'file-dialog DOS workflows')
if __name__=='__main__':main()
