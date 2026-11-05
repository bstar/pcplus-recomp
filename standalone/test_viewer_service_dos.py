#!/usr/bin/env python3
"""Verify live serial parsing/CPR beneath the full-screen file viewer in DOS8086."""
import argparse,json,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import sha
from test_viewer_dialog_dos import page
ROOT=harness.ROOT

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_file_viewer'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);observer=out/'VIEWOBS.COM';subprocess.run(['nasm','-fbin','-DWATCH_KIND=8',str(ROOT/'standalone/viewer_dialog_watch.asm'),'-o',str(observer)],check=True)
 harness.BINARY=binary;settings=bytearray(prm(port=3,baud=5))
 for at,val in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,val)
 label=out.name+'-serviced';drive=ROOT/'build/connection-dos'/label;assert not drive.exists()
 payload=b''.join(('L%03d\r\n'%i).encode() for i in range(1,73));message=b'UART-WHILE-VIEW'
 base=harness.run(label,'success','p900 enter p3500 a-v p500 p a g e . d a t enter p6500 escape p900 r e a d y enter p1000 a-x',
  prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='VIEWOBS',timeout=35,
  files={'VIEWOBS.COM':observer.read_bytes(),'PAGE.DAT':payload},
  online_updates=((5.0,b'\x1b[23;1H'+message+b'\x1b[6n'),),online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-VIEWER\x1b[6n'),))
 raw=(drive/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw);before=raw[18:4018];local=raw[4018:8018];after=raw[8018:12018]
 expected=bytearray(before)
 for i,c in enumerate(message):expected[(22*80+i)*2:(22*80+i)*2+2]=bytes([c,7])
 wire=(drive/'serial.bin').read_bytes();checks={**base['checks'],
  'observer_and_vector_restore':len(raw)==12083 and words[0]==0x5656 and words[1]==15,
  'exact_local_page':local==page([('L%03d'%i).encode() for i in range(1,25)]),
  'incoming_query_while_viewer_open':b'\x1b[23;16R' in wire,
  'exact_updated_live_frame_after_escape':after==expected,
  'updated_live_cursor_after_escape':words[7]==(22<<8)|len(message) and words[8]==words[4],
  'later_query_and_keyboard':b'\x1b[3;13R' in wire and wire.count(b'ready\r')==1,
  'owned_file_unchanged':(drive/'PAGE.DAT').read_bytes()==payload,
  'CWD_unchanged':raw[12018]==3 and raw[12019:].split(b'\0',1)[0]==b''}
 r=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),capture_sha256=sha(drive/'VIEWUI.BIN'),observer_words=words,
  sources={n:sha(ROOT/n) for n in ['standalone/test_viewer_service_dos.py','standalone/test_viewer_dialog_dos.py','standalone/viewer_dialog_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py']},original_inputs=[],
  scope=__doc__+' Actual COM3/IRQ5 DOS terminal, synthetic peer, passive local/before/after VGA/BDA capture and updated live-frame/cursor restoration. Incoming bytes and fresh DSR while local view is open. No SIP/DSP/physical, stock editor or capture/printer pressure claim.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'],r
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 print('PASS serviced viewer and exact updated live-frame/cursor restoration')
if __name__=='__main__':main()
