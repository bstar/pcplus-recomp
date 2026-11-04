#!/usr/bin/env python3
"""Actual DOS UART size reply -> staged SynthModem proxy -> real loopback NAWS.
No installed configuration, service, SIP, DSP, analog modem or BBS acceptance.
"""
import argparse,hashlib,json,os,struct,subprocess,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'lab/bbs/patches/synthmodem-menu-size'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--display-rows',type=int,choices=[25,28,43,50]);p.add_argument('--status-hidden',type=int,choices=[0,1],default=0);a=p.parse_args()
 stage=a.stage.resolve();terminal=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 candidate_inputs={str(p.relative_to(stage)):sha(p) for p in (stage/'candidate').rglob('*') if p.is_file()}
 receipt=json.loads((stage/'result.json').read_text());assert receipt['passed']
 for name,h in receipt['candidate'].items():assert sha(stage/'candidate'/name)==h,name
 for name,h in receipt['sources'].items():assert sha(ROOT/name)==h,name
 manifest=json.loads((terminal.parent/'manifest.json').read_text());assert manifest['experimental_window_size_report'] and sha(terminal)==manifest['binary_sha256']
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'dos-peer.js',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py',ROOT/'standalone/display_startup_geometry.asm']}
 physical=a.display_rows or 25;logical=physical-(not a.status_hidden)
 assert a.display_rows or a.status_hidden==0,'Hidden status requires an explicit startup layout'
 if a.display_rows:assert manifest['experimental_display_startup'],'Explicit layouts require imported display startup'
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 # Generic modem fixtures contain filler display words. Startup-enabled
 # parents require an explicitly valid owned25-row default as well.
 if a.display_rows or manifest.get('experimental_display_startup'):
  for at,value in [(0x1c2,a.status_hidden),(0x1c8,2),(0x1ca,physical),(0x4ec,0)]:struct.pack_into('<H',raw,at,value)
 (out/'TEST.PRM').write_bytes(raw)
 sampler=SAMPLER.replace('mov cx,4000','mov cx,8000') if a.display_rows else SAMPLER
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/display_startup_geometry.asm'),'-o',str(out/'GEOM.COM')],check=True)
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(0x3e8+offset))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-f','bin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 with (out/'peer.log').open('w') as log:
  peer=subprocess.Popen(['node',str(HERE/'dos-peer.js'),str(stage/'candidate'),str(out)],stdout=log,stderr=log)
  try:
   deadline=time.monotonic()+5
   while not (out/'ready.json').exists():
    assert peer.poll() is None,'peer exited';assert time.monotonic()<deadline,'peer startup deadline';time.sleep(.01)
   port=json.loads((out/'ready.json').read_text())['port']
   cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=nullmodem server:127.0.0.1 port:{port} transparent:1 irq:5 rxdelay:200 txdelay:1
serial4=disabled
[autoexec]
@echo off
mount c "{terminal.parent}"
mount d "{out}"
d:
set PCPLUS=
D:\\SNAP B
ADDKEY p900 enter p5000 l o c enter p2000 z p1500 a-x
C:\\TERMINAL @D:\\TEST.PRM /D:1 /I:3
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\GEOM
D:\\SNAP S
D:\\SNAP A
exit
'''
   (out/'dosbox.conf').write_text(cfg)
   with (out/'dosbox.log').open('w') as doslog:
    dos=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=doslog,stderr=doslog,timeout=30)
   peer.wait(timeout=5)
  finally:
   if peer.poll() is None:
    peer.terminate()
    try:peer.wait(timeout=5)
    except subprocess.TimeoutExpired:peer.kill();peer.wait()
 state=json.loads((out/'peer-result.json').read_text());wire=(out/'serial-in.bin').read_bytes();screen=(out/'SCREEN.BIN').read_bytes();app=(out/'application-in.bin').read_bytes()
 checks=dict(DOS_exit=dos.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),peer_exit=peer.returncode==0,no_peer_errors=not state['errors'],numeric_dial_only=state['commands']==['ATZ','ATD1'],one_owned_query=state['queries']==1,one_tcp_connection=state['tcpConnections']==1,actual_size_reply=wire.count(b'\x1b'+f'[8;{logical};80t'.encode())==1,accepted_NAWS=state['dimensions']==[dict(cols=80,rows=logical)],actual_CPR=b'\x1b[1;16R' in app,actual_DA=b'\x1b[?1;2c' in app,typed_keyboard=b'z' in app,metadata_consumed=b'\x1b[8;' not in app,immediate_banner=len(screen)==(8000 if a.display_rows else 4000) and screen[:30:2]==b'FIRST BYTE SAFE',hardware_restored=len((out/'BEFORE.BIN').read_bytes())==42 and (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes(),PRM_unchanged=(out/'TEST.PRM').read_bytes()==raw,terminal_unchanged=sha(terminal)==manifest['binary_sha256'])
 geometry=struct.unpack('<4H',(out/'GEOM.BIN').read_bytes())
 checks['actual_BIOS_layout']=geometry==(physical,14 if physical==28 else 8 if physical in (43,50) else 16,0x5003,geometry[3]) and geometry[3]>>8==0
 checks['bottom_logical_row']=screen[(logical-1)*160:(logical-1)*160+22:2]==b'BRIDGE-AREA'
 last=screen[(physical-1)*160:physical*160:2]
 checks['status_row']=last.startswith(b'BRIDGE-AREA') if a.status_hidden else last.startswith(b' Disconnected  ') and b'ANSI' in last and b'19200 N81' in last
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 for name,h in receipt['sources'].items():assert sha(ROOT/name)==h,name
 for name,h in inputs.items():assert sha(ROOT/name)==h,name
 assert candidate_inputs=={str(p.relative_to(stage)):sha(p) for p in (stage/'candidate').rglob('*') if p.is_file()}
 report=dict(passed=all(checks.values()),checks=checks,physical_rows=physical,logical_rows=logical,status_hidden=a.status_hidden,terminal_sha256=sha(terminal),terminal_manifest_sha256=sha(terminal.parent/'manifest.json'),stage_receipt_sha256=sha(stage/'result.json'),sources=inputs,artifacts={name:sha(out/name) for name in ['peer-result.json','serial-in.bin','serial-out.bin','tcp-in.bin','application-in.bin','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','TEST.PRM','GEOM.COM','GEOM.BIN','sampler.asm','SNAP.COM','dosbox.conf']},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],json.dumps(report,indent=2)
 print('PASS actual8086 DOS COM3/IRQ5 query reply, real staged proxy NAWS and post-connect CPR/DA/keyboard')
if __name__=='__main__':main()
