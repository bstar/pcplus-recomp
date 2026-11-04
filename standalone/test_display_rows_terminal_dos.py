#!/usr/bin/env python3
"""Exercise the banked BIOS row owner in the real DOS parent before UART enable."""
import argparse,hashlib,json,os,socket,struct,subprocess,sys,threading
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary,out=a.terminal.resolve(),a.output.resolve();assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 out.mkdir(parents=True,exist_ok=False);m=json.loads((binary.parent/'manifest.json').read_text())
 assert m['diagnostic_display_row_probe'] and m['experimental_display_row_owner'] and not m['diagnostic_status_probe']
 geometry=bool(m.get('diagnostic_row_geometry_probe'));leaf='GROWS.BIN' if geometry else 'DROWS.BIN'
 assert sha(binary)==m['binary_sha256']
 for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
 runs={};states=[]
 for label in ('normal','exclusive'):
  run=out/label;run.mkdir();drive=run/'drive';drive.mkdir();raw=bytearray(fixture(timeout=5))
  struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
  struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0)
  struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
  if m.get('experimental_display_preferences'):
   for at,value in ((0x1c2,0xffff),(0x1c8,4),(0x1ca,43),(0x4ec,0x12)):struct.pack_into('<H',raw,at,value)
  (drive/'TEST.PRM').write_bytes(raw)
  sentinel=b'Keep this existing diagnostic file.\x00\xff'
  if label=='exclusive':(drive/leaf).write_bytes(sentinel)
  sampler=SAMPLER
  for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(0x3e8+offset))
  (drive/'SNAP.ASM').write_text(sampler);subprocess.run(['nasm','-fbin',str(drive/'SNAP.ASM'),'-o',str(drive/'SNAP.COM')],check=True)
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.1)
  stop=threading.Event();wire=bytearray();accepted=[];errors=[]
  def peer():
   connection=None
   try:
    while not stop.is_set() and connection is None:
     try:connection,_=server.accept();connection.settimeout(.1);accepted.append(True)
     except socket.timeout:pass
    while not stop.is_set() and connection is not None:
     try:
      data=connection.recv(4096)
      if not data:break
      wire.extend(data)
     except socket.timeout:pass
   except OSError as error:
    if not stop.is_set():errors.append(str(error))
   finally:
    if connection is not None:connection.close()
  thread=threading.Thread(target=peer,daemon=True);thread.start()
  expected='if errorlevel 24 goto failed\nif errorlevel 23 goto passed\ngoto failed\n' if label=='exclusive' else 'if errorlevel 1 goto failed\ngoto passed\n'
  config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 irq:5 rxdelay:200 txdelay:1
serial4=disabled
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{drive}"
d:
set PCPLUS=D:\\
SNAP B
ADDKEY p900 enter
C:\\TERMINAL @D:\\TEST.PRM /D:Unused:23 /I:3
{expected}:passed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP S
SNAP A
exit
'''
  (run/'dosbox.conf').write_text(config)
  try:
   with (run/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=35)
  finally:stop.set();server.close();thread.join(2)
  assert not thread.is_alive() and not errors and accepted and not wire,(errors,wire)
  assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),label
  before,after=(drive/'BEFORE.BIN').read_bytes(),(drive/'AFTER.BIN').read_bytes()
  assert len(before)==42 and before==after,'IRQ/UART/PIC restoration failed'
  assert (drive/'TEST.PRM').read_bytes()==raw
  if m.get('experimental_display_preferences'):
   assert (drive/'DPREF.BIN').read_bytes()==struct.pack('<5H',1,0xffff,4,43,0x12)
   selected=struct.unpack('<131H',(drive/'DSEL.BIN').read_bytes());assert selected[:3]==(0x4453,1,8)
   for i,(selector,physical,status,accepted,fallback) in enumerate(((1,25,0,1,0),(2,43,0,2,0),(0,43,0,0,0),(3,25,0,3,0),(4,50,0,4,0),(3,25,0,1,1),(4,25,0,1,1),(3,25,3,1,1))):
    rec=selected[3+i*16:3+(i+1)*16]
    assert rec[0]==selector and rec[3]==status and rec[4:7]==(3,80,physical)
    assert rec[7:10]==(0xb800,160,physical*80) and rec[13:]==(fallback,selector,accepted)

  if m.get('experimental_display_preferences'):
   composed=struct.unpack('<102H',(drive/'TSEL.BIN').read_bytes());assert composed[:3]==(0x5453,1,9)
   for i,(physical,selector,fallback,result,hidden) in enumerate(((25,1,0,0,0),(43,2,0,0,0),(43,0,0,0,0),(25,3,0,0,0),(50,4,0,0,0),(25,1,1,0,0),(25,1,1,0,0),(25,1,1,3,0),(25,1,1,3,1))):
    rec=composed[3+i*11:3+(i+1)*11];effective=physical if hidden else physical-1
    assert rec[3:]==(0,physical,effective,hidden,selector,1,fallback,result)
    video=(drive/f'SV{i}.BIN').read_bytes();shadow=(drive/f'SW{i}.BIN').read_bytes()
    assert len(video)==physical*160 and len(shadow)==8192
    assert video[:effective*160]==b' \x07'*(effective*80)
    if not hidden:assert b'Alt-Z FOR HELP' in video[effective*160::2]
    assert shadow[:len(video)]==video and shadow[len(video):]==bytes(8192-len(video))
  observed=(drive/leaf).read_bytes()
  if label=='exclusive':assert observed==sentinel
  else:
   width=21 if geometry else 18;word_count=3+6*width
   assert len(observed)==word_count*2
   words=struct.unpack('<'+'H'*word_count,observed);assert words[:3]==(0x4452,2 if geometry else 1,6)
   states=[words[3+i*width:3+(i+1)*width] for i in range(6)]
   for phase,(state,request,rows) in enumerate(zip(states,(0,25,28,43,50,25),(25,25,28,43,50,25))):
    assert state[:5]==(request,0,3,80,rows),state
    assert state[5:10]==(0xb800,160,rows*80,1,1),state
    assert state[11]==0 and state[12]==0x5003 and state[13]>>8==0
    effective=rows-1 if geometry else 24
    assert state[14:18]==(rows-1,effective,effective-1,0),'BIOS or canonical geometry differs'
    if geometry:
     assert state[19:]==((rows-1)*160,(rows-1)*256)
     video=(drive/f'GV{phase}.BIN').read_bytes();shadow=(drive/f'GW{phase}.BIN').read_bytes()
     assert len(video)==rows*160 and len(shadow)==8192
     if phase:
      assert video[:effective*160]==bytes([32,state[18]&255])*(effective*80)
      assert b'Alt-Z FOR HELP' in video[effective*160::2]
      assert shadow[:len(video)]==video and shadow[len(video):]==bytes(8192-len(video))
  runs[label]=dict(passed=True,expected_exit=23 if label=='exclusive' else 0,hardware_snapshot_bytes=42,
   connected_virtual_serial=True,serial_output_bytes=len(wire),artifacts={str(f.relative_to(run)):sha(f) for f in run.rglob('*') if f.is_file()})
 from package_connection_test import stage
 try:stage(out/'must-not-package',{'TERMINAL.EXE':binary})
 except AssertionError as error:assert 'Startup diagnostic' in str(error)
 else:raise AssertionError('Startup diagnostic accepted as an application payload')
 assert not (out/'must-not-package').exists()
 assert sha(binary)==m['binary_sha256']
 for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
 inputs={n:sha(ROOT/n) for n in ('standalone/test_display_rows_terminal_dos.py','standalone/modem_fixtures.py','standalone/test_terminal.py','standalone/package_connection_test.py')}
 record=dict(passed=True,terminal_sha256=m['binary_sha256'],manifest_sha256=sha(binary.parent/'manifest.json'),checker_inputs=inputs,
  bank=m['display_row_bank'],states=states,runs=runs,diagnostic_package_rejected=True,canonical_geometry_transaction=geometry,display_preferences_captured=bool(m.get('experimental_display_preferences')),
  scope=('Actual8086 DOS source-built parent calls real offline BIOS/canonical/RIS transaction at startup before UART enable; six BIOS/effective-row observations with actual video/full-shadow captures and native status at physical bottom.' if geometry else 'Actual8086 DOS source-built parent calls low-level DISPLAY_CODE API before UART enable; six BIOS observations with canonical geometry intentionally unchanged24.')+' Exclusive output refusal returns23 and preserves existing file. Both COM3/IRQ5 virtual-UART/PIC/vector snapshots restore; zero serial commands. No actual live RX/parser during transaction, hardware-fault injection in DOS, normal key/menu, online/BBS/SIP or physical acceptance. Diagnostic cannot be packaged.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS linked DOS rows:6 observations, exclusive create refusal, hardware restore, diagnostic package rejection; canonical transaction',geometry)
if __name__=='__main__':main()
