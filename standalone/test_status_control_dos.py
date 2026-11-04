#!/usr/bin/env python3
"""Actual8086 DOS normal Ctrl-]/Alt-Z status controls and serial area reports.
Synthetic loopback serial peer; no online resize, BBS, SIP or physical claim.
"""
import argparse,hashlib,json,re,struct,inspect,types,subprocess
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],default=25);a=p.parse_args()
 assert re.fullmatch('[a-z0-9-]+',a.label);binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_status_control'] and m['experimental_window_size_report'];assert sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 assert (m.get('diagnostic_session_rows_probe') or 25)==a.rows
 out=ROOT/'build/status-control-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
 folder=ROOT/'build/connection-dos'/a.label;assert not folder.exists()
 observer=(ROOT/'standalone/pause_watch.asm').read_text()
 for old,new in [("message: db 'Screen paused.  Press any key to continue...'","message: db 'EXPOSED'"),('mov di,(PAUSE_ROWS-1)*160+18*2','mov di,(PAUSE_ROWS-1)*160'),('mov cx,44','mov cx,7'),('cmp word [cs:pause_ticks],18','cmp word [cs:pause_ticks],1')]:
  assert observer.count(old)==1,old;observer=observer.replace(old,new)
 (out/'status-watch.asm').write_text(observer)
 subprocess.run(['nasm','-fbin','-DPAUSE_ROWS='+str(a.rows),str(out/'status-watch.asm'),'-o',str(out/'STATW.COM')],check=True)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 # Clone the owned harness only to capture all8000 physical bytes; its existing
 # serial peer, DOS process and hardware checks remain unchanged.
 owned=types.ModuleType('full_status_harness');owned.__dict__.update(harness.__dict__);owned.BINARY=binary
 owned.SAMPLER=harness.SAMPLER.replace('mov cx,4000','mov cx,8000')
 source=inspect.getsource(harness.run);assert source.count('len(screen)==4000')==1
 source=source.replace('len(screen)==4000','len(screen)==8000');exec(compile(source,harness.__file__,'exec'),owned.__dict__)
 response=b'\x1b[18t\x1b[99;80H\x1b[6n\x1b[99;1HEXPOSED\x1b[1;16H'
 result=owned.run(a.label,'direct','p900 enter p1500 a p500 c-] p500 b p500 a-z p400 c-] p400 c p700 a-x',prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',arguments='@D:\\TEST.PRM /I:3',timeout=25,online_triggers=((b'a',response),(b'b',response),(b'c',response)),files={'STATW.COM':(out/'STATW.COM').read_bytes()},observer='STATW')
 wire=(folder/'serial.bin').read_bytes();sizes=re.findall(rb'\x1b\[8;(\d+);(\d+)t',wire)
 screen=(folder/'SCREEN.BIN').read_bytes();visible=a.rows-1
 frames=(folder/'PAUSE.BIN').read_bytes();size=a.rows*160
 result['checks'].update(three_requested_area_reports=sizes==[(str(visible).encode(),b'80'),(str(a.rows).encode(),b'80'),(str(visible).encode(),b'80')],CPR_hidden_area=b'\x1b'+f'[{a.rows};80R'.encode() in wire,CPR_visible_area=wire.count(b'\x1b'+f'[{visible};80R'.encode())==2,Ctrl_bracket_never_transmitted=b'\x1d' not in wire,full_physical_capture=len(screen)==8000,last_logical_row_written=screen[(a.rows-2)*160:(a.rows-2)*160+14:2]==b'EXPOSED',status_on_last_physical_row=b'Alt-Z FOR HELP' in screen[(a.rows-1)*160:a.rows*160:2],two_full_exposed_frames=len(frames)==size*2,exposed_last_row_rendered=all(frames[at+size-160:at+size-146:2]==b'EXPOSED' for at in (0,size)))
 result['passed']=all(result['checks'].values())
 record=dict(passed=result['passed'],checks=result['checks'],rows=a.rows,terminal_sha256=sha(binary),terminal_manifest_sha256=sha(binary.parent/'manifest.json'),area_reports=[list(map(lambda b:int(b),s)) for s in sizes],parent_result=str((folder/'result.json').relative_to(ROOT)),sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py',ROOT/'standalone/pause_watch.asm']},artifacts={str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()},scope=__doc__+' Passive timer witnesses actual rendering on the temporarily exposed physical row; final full-frame capture verifies returned status/body placement.')
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');assert record['passed'],json.dumps(record,indent=2)
 print('PASS actual DOS BIOS Ctrl-] and Alt-Z, rows',visible,a.rows,visible,'CPR/lower cells and hardware restoration')
if __name__=='__main__':main()
