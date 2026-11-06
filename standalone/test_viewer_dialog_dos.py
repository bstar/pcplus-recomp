#!/usr/bin/env python3
"""Exercise real terminal Alt-V prompt/pages/errors/menu and exact live-screen return."""
import argparse,json,os,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import sha
ROOT=harness.ROOT
FOOTER=b' Home: Top of file      PgUp: Previous page      PgDn: Next page      ESC: Exit '

def page(rows):
 lines=rows+[b'']*(24-len(rows))+[FOOTER]
 return b''.join(bytes((c,0x71 if i==24 else 7)) for i,row in enumerate(lines) for c in row.ljust(80,b' '))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case');p.add_argument('--internal-fallback',action='store_true');a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();m=json.loads(binary.with_name('manifest.json').read_text())
 assert m['experimental_file_viewer'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);harness.BINARY=binary;settings=bytearray(prm(port=3,baud=5))
 for at,val in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,val)
 if a.internal_fallback:
  assert m['experimental_external_viewer']
  settings[0x35d:0x39e]=bytes(65)
 lines=b''.join(('L%03d\r\n'%i).encode() for i in range(1,73))
 binary_text=b'TAB\tMID\r\nC\rR\nNUL\0HIDDEN\r\nZ\x1aAFTER\r\nE\x1b[31mRED\r\n'+bytes([0x80,0x81,0xdb,0xb0,0xff])+b'\r\nTRAIL  \t\x1a\r\n \t\r\n'
 recipes=[('cancel',1,'a-v p1200 escape'),('page',2,'a-v p500 p a g e . d a t enter p1500 escape'),
  ('next',3,'a-v p500 p a g e . d a t enter p1100 pgdown p1500 escape'),
  ('home',7,'a-v p500 p a g e . d a t enter p900 pgdown p900 home p1500 escape'),
  ('missing',4,'a-v p500 n o f i l e . x enter p1500 space p400 escape'),
  ('binary',5,'a-v p500 b i n a r y . d a t enter p1500 escape'),
  ('empty',6,'a-v p500 e m p t y . d a t enter p1500 escape'),
  ('reference',2,'a-z p500 a-v p500 p a g e . d a t enter p1500 escape'),
  ('browser',2,'` p500 v p500 p a g e . d a t enter p1500 escape'),
  ('loading-cancel',1,'a-v p1000 p a g e . d a t enter escape p800')]
 cases=[]
 for name,kind,keys in recipes:
  if a.case and name!=a.case:continue
  observer=out/(name+'.COM');subprocess.run(['nasm','-fbin','-DWATCH_KIND='+str(kind),str(ROOT/'standalone/viewer_dialog_watch.asm'),'-o',str(observer)],check=True)
  label=out.name+'-'+name;drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
  base=harness.run(label,'success','p900 enter p3500 '+keys+' p700 r e a d y enter p1000 a-x',
   prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',
   files={'VIEWOBS.COM':observer.read_bytes(),'PAGE.DAT':lines,'BINARY.DAT':binary_text,'EMPTY.DAT':b''},
   observer='VIEWOBS',timeout=35,online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-VIEWER\x1b[6n'),))
  raw=(drive/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw);before=raw[18:4018];frame=raw[4018:8018];after=raw[8018:12018]
  wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
  checks={**base['checks'],'passive_before_target_after_and_vector_restore':len(raw)==12083 and words[0]==0x5656 and words[1]==15,
   'exact_terminal_frame_restore':before==after,'exact_cursor_and_shape_restore':words[3:5]==words[7:9],
   'drive_and_CWD_restored':raw[12018]==3 and raw[12019:].split(b'\0',1)[0]==b'',
   'keyboard_after_viewer':wire.count(b'ready\r')==1,'post_view_query':b'\x1b[3;13R' in wire,
   'post_view_display':screen[320:344:2]==b'AFTER-VIEWER'}
  if kind==1:
   checks['original_prompt_geometry']=frame[(10*80+9)*2:(10*80+9)*2+2]==b'\xb5\x0b' and b'Please enter filename:' in frame[::2]
   checks['prompt_cursor']=words[5:7]==(0x0c1e,words[4])
  elif kind==4:checks['not_found']=frame[(12*80+7)*2:(12*80+24)*2:2]==b'FILE NOT FOUND...'
  else:
   expected=page([('L%03d'%i).encode() for i in range(25,49)] if kind==3 else [] if kind==6 else
    [b'TAB\tMID',b'C\rR',b'NUL',b'Z\x1aAFTER',b'E\x1b[31mRED',bytes([0x80,0x81,0xdb,0xb0,0xff]),b'TRAIL'] if kind==5 else [('L%03d'%i).encode() for i in range(1,25)])
   checks['exact_2000_view_cells']=frame==expected;checks['offscreen_cursor_original_shape']=words[5:7]==(0x64c8,words[4])
  r=dict(case=name,passed=all(checks.values()),checks=checks,capture_sha256=sha(drive/'VIEWUI.BIN'),observer_words=words)
  cases.append(r);(out/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n');assert r['passed'],r
 assert cases
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 names=['standalone/test_viewer_dialog_dos.py','standalone/viewer_dialog_watch.asm','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/directory_fixtures.py']
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in names},original_inputs=[],
  scope=__doc__+' Actual8086 COM3/IRQ5 synthetic serial peer, owned files, real DOS reads/seeks/close, passive VGA/BDA before-target-after captures, exact full-frame/cursor return and post-dialog keyboard/CPR plus hardware restoration. No physical modem/SIP/DSP or configured external-viewer acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'terminal viewer workflows')
if __name__=='__main__':main()
