#!/usr/bin/env python3
"""Actual DOS8086 foreground status transaction diagnostic; no BBS/modem session."""
import argparse,hashlib,json,os,socket,struct,subprocess,sys,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['diagnostic_status_probe'] and manifest['experimental_status_owner']
 assert sha(binary)==manifest['binary_sha256']
 for source,digest in manifest['sources'].items():assert sha(ROOT/source)==digest,source
 drive=out/'drive';drive.mkdir();raw=bytearray(fixture(timeout=5))
 struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0)
 struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 (drive/'TEST.PRM').write_bytes(raw)
 sampler=SAMPLER
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(0x3e8+offset))
 (drive/'SNAP.ASM').write_text(sampler);subprocess.run(['nasm','-fbin',str(drive/'SNAP.ASM'),'-o',str(drive/'SNAP.COM')],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.1)
 stop=threading.Event();wire=bytearray();sent=[];errors=[]
 stages=[('T1.BIN',44,b'\x1b[25;8H\x1b7'),('T3.BIN',44,b'\x1b[6;80HA'),('R4.BIN',2,b'X'),('T4.BIN',44,b'\x1b[6;80HA'),('R5.BIN',2,b'Y')]
 def peer():
  connection=None;index=0;deadline=time.monotonic()+35
  try:
   while not stop.is_set() and time.monotonic()<deadline:
    if connection is None:
     try:connection,_=server.accept();connection.settimeout(.02)
     except socket.timeout:continue
    if index<len(stages):
     leaf,size,payload=stages[index];marker=drive/leaf
     if marker.exists() and marker.stat().st_size==size:
      connection.sendall(payload);sent.append(dict(marker=leaf,payload_hex=payload.hex()));index+=1
    try:
     data=connection.recv(4096)
     if not data:
      if index!=len(stages):errors.append('Connection ended before all diagnostic stages')
      return
     wire.extend(data)
    except socket.timeout:pass
   if not stop.is_set():errors.append('Diagnostic peer deadline')
  except OSError as error:
   if not stop.is_set():errors.append(str(error))
  finally:
   if connection is not None:connection.close()
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 cfg='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[serial]\nserial1=disabled\nserial2=disabled\nserial3=dummy irq:5\nserial4=disabled\n[autoexec]\n@echo off\n'
 cfg=cfg.replace('serial3=dummy irq:5','serial3=nullmodem server:127.0.0.1 port:'+str(server.getsockname()[1])+' transparent:1 irq:5 rxdelay:200 txdelay:1')
 cfg+='mount c "'+str(binary.parent)+'"\nmount d "'+str(drive)+'"\nd:\nset PCPLUS=D:\\\nSNAP B\nADDKEY p900 enter\nC:\\TERMINAL @D:\\TEST.PRM /D:Unused:23 /I:3\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto capture\n:failed\necho FAIL>FAIL.TXT\n:capture\nSNAP S\nSNAP A\nexit\n'
 (out/'dosbox.conf').write_text(cfg)
 try:
  with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=35)
 finally:stop.set();server.close();thread.join(2)
 (out/'peer.json').write_text(json.dumps(dict(sent=sent,errors=errors,wire_hex=wire.hex()),indent=2)+'\n')
 assert not thread.is_alive() and not errors,errors
 assert len(sent)==5 and not wire,(sent,bytes(wire))
 assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),'Diagnostic did not return success; inspect DOS log and staged state files'
 before=(drive/'BEFORE.BIN').read_bytes();after=(drive/'AFTER.BIN').read_bytes();assert len(before)==42 and before==after,'IRQ vectors/UART/PIC not restored'
 assert (drive/'TEST.PRM').read_bytes()==raw and sha(binary)==manifest['binary_sha256']
 states=[];screens=[]
 for phase in range(6):
  data=(drive/f'T{phase}.BIN').read_bytes();assert len(data)==44;state=struct.unpack('<22H',data);assert state[0]==phase and state[1]==0 and state[18]==24 and state[19]==0
  rows=25 if phase in (1,4) else 24
  assert state[2]==state[16]==rows and state[3]==state[4]==state[5]==rows-1 and state[6]==rows*80 and state[7]==int(rows==25)
  assert state[8]==state[10] and state[9]==state[11]
  assert state[12]==state[8]*160+state[9]*2 and state[13]==state[8]*80+state[9]
  screen=(drive/f'S{phase}.BIN').read_bytes();assert len(screen)==4000;states.append(state);screens.append(screen)
 assert screens[0]==b''.join(bytes([65+row,7])*80 for row in range(25))
 assert screens[1][:3840]==screens[0][:3840] and screens[1][3840:]==bytes([32,states[1][20]&255])*80
 assert screens[2][:3840]==screens[1][160:] and b'Alt-Z FOR HELP' in screens[2][3840::2]
 assert states[2][8:14]==(23,7,23,7,3694,1847) and states[2][14]==23 and states[2][17]==0x1707
 assert screens[3][:3840]==bytes([32,states[3][21]&255])*1920 and states[3][8:14]==(0,0,0,0,0,0)
 for phase,character in ((4,ord('X')),(5,ord('Y'))):
  assert screens[phase][6*160]==character and states[phase][8:14]==(6,1,6,1,962,481) and states[phase][15]==0
 assert b'Alt-Z FOR HELP' in screens[5][3840::2]
 # Prove a startup diagnostic cannot silently become an application package.
 from package_connection_test import stage
 try:stage(out/'must-not-package',{'TERMINAL.EXE':binary})
 except AssertionError as error:assert 'Startup diagnostic' in str(error)
 else:raise AssertionError('Diagnostic packaging was accepted')
 assert not (out/'must-not-package').exists()
 for source,digest in manifest['sources'].items():assert sha(ROOT/source)==digest,source
 sources=dict(manifest['sources']);sources['standalone/test_status_transition_dos.py']=sha(Path(__file__));sources['standalone/modem_fixtures.py']=sha(ROOT/'standalone/modem_fixtures.py');sources['standalone/test_terminal.py']=sha(ROOT/'standalone/test_terminal.py');sources['standalone/package_connection_test.py']=sha(ROOT/'standalone/package_connection_test.py')
 result=dict(passed=True,diagnostic_terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),sources=sources,states=states,serial_inputs=sent,serial_output_sha256=hashlib.sha256(wire).hexdigest(),
  checks=dict(actual_DOS8086_foreground=True,six_observed_states=True,hide_show_pixels=True,native_scroll_and_cursor_offsets=True,real_RIS_defaults=True,deferred_wrap_hide_and_show=True,hardware_restored=True,private_fixture_unchanged=True,binary_unchanged=True,diagnostic_package_rejected=True,actual_virtual_UART_RX=True,no_outbound_modem_commands=True),
  artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__+' Diagnostic invokes actual unchanged transaction/native/parser/RIS services after normal startup capture with UART enabled but before dial, then ordinary shutdown restores IRQ/UART/PIC. COM3/IRQ5 actual virtual UART/IRQ and ordinary parent receive/parser path with loopback ANSI peer; no modem/carrier, SynthModem/BBS/SIP/DSP/analog or physical acceptance. Separate diagnostic binary, not the ordinary application identity.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS actual DOS8086:6 states, native scroll/cursor/RIS/wrap, pixels and hardware restoration')
if __name__=='__main__':main()
