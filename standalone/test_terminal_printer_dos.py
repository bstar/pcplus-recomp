#!/usr/bin/env python3
"""Independent live PRN verification with DOSBox-X file-only parallel output.

All DOS programs/media are source-built and owned; never accesses host printers.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from test_terminal import SAMPLER
from test_terminal_monitor_dos import MonitorPeer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal-printer-dos'
BINARY=ROOT/'build/terminal/TERMINAL.EXE'
PROBE=r'''bits 16
org 100h
push cs
pop ds
mov dx,device
mov ax,3d02h
int 21h
pushf
pop word [open_flags]
mov [open_ax],ax
jc save
mov bx,ax
mov [handle],ax
mov ax,4400h
int 21h
pushf
pop word [info_flags]
mov [info_ax],ax
mov [old_info],dx
and dx,0ffh
or dx,20h
mov ax,4401h
int 21h
pushf
pop word [set_flags]
mov [set_ax],ax
mov ax,4407h
int 21h
pushf
pop word [ready_flags]
mov [ready_ax],ax
jc close
cmp al,0ffh
jne close
mov dx,payload
mov cx,256
mov ah,40h
int 21h
pushf
pop word [write_flags]
mov [write_ax],ax
close:
mov bx,[handle]
mov dx,[old_info]
and dx,0ffh
mov ax,4401h
int 21h
mov ah,3eh
int 21h
pushf
pop word [close_flags]
mov [close_ax],ax
save:
mov dx,report
xor cx,cx
mov ah,3ch
int 21h
jc done
mov bx,ax
mov dx,state
mov cx,state_end-state
mov ah,40h
int 21h
mov ah,3eh
int 21h
done:
mov ax,4c00h
int 21h
device db 'PRN',0
report db 'PROBE.BIN',0
state:
open_flags dw 0ffffh
open_ax dw 0ffffh
info_flags dw 0ffffh
info_ax dw 0ffffh
old_info dw 0ffffh
set_flags dw 0ffffh
set_ax dw 0ffffh
ready_flags dw 0ffffh
ready_ax dw 0ffffh
write_flags dw 0ffffh
write_ax dw 0ffffh
close_flags dw 0ffffh
close_ax dw 0ffffh
state_end:
handle dw 0
payload:
%assign i 0
%rep 256
db i
%assign i i+1
%endrep
'''
def dos_run(out,parallel,autoexec,timeout=25):
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[parallel]\nparallel1={parallel}\nparallel2=disabled\nparallel3=disabled\n[serial]\nserial1=disabled\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount d "{out}"\nd:\n{autoexec}\nexit\n'''
 (out/'dosbox.conf').write_text(conf)
 with (out/'dosbox.log').open('w') as log:
  return subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=timeout).returncode

def probe(label):
 base=OUT/label;base.mkdir(parents=True,exist_ok=False);rows=[]
 keydir=base/'key';keydir.mkdir();keysource="""bits 16
org 100h
xor ah,ah
int 16h
mov [value],ax
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
mov bx,ax
mov dx,value
mov cx,2
mov ah,40h
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
value dw 0
name db 'KEY.BIN',0
"""
 (keydir/'KEY.asm').write_text(keysource);subprocess.run(['nasm','-fbin',str(keydir/'KEY.asm'),'-o',str(keydir/'KEY.COM')],check=True);dos_run(keydir,'disabled','ADDKEY a-l\nKEY');assert (keydir/'KEY.BIN').read_bytes()==b'\x00\x26','AltL BIOS word differs'

 for mode in ('file','disabled'):
  out=base/mode;out.mkdir();(out/'PROBE.asm').write_text(PROBE);subprocess.run(['nasm','-fbin',str(out/'PROBE.asm'),'-o',str(out/'PROBE.COM')],check=True)
  code=dos_run(out,f'file append:{out}/PRINTER.RAW' if mode=='file' else 'disabled','PROBE')
  raw=(out/'PROBE.BIN').read_bytes();words=[int.from_bytes(raw[i:i+2],'little') for i in range(0,len(raw),2)];wire=(out/'PRINTER.RAW').read_bytes() if (out/'PRINTER.RAW').exists() else b''
  checks=dict(DOS_exit=code==0,report_extent=len(raw)==26)
  if mode=='file':checks.update(actual_PRN_open=not words[0]&1,character_device=bool(words[4]&128),binary_set=not words[5]&1,ready=not words[7]&1 and words[8]&255==255,write_count=not words[9]&1 and words[10]==256,close_ok=not words[11]&1,exact_all256=wire==bytes(range(256)))
  else:checks.update(unavailable_open=bool(words[0]&1) and words[1]==2,no_output=not wire)
  result=dict(passed=all(checks.values()),checks=checks,mode=mode,returncode=code,words=words,raw_size=len(wire),raw_sha256=hashlib.sha256(wire).hexdigest(),exact_all256=wire==bytes(range(256)))
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');rows.append(result)
 (base/'probe.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2));return 0 if all(r['passed'] for r in rows) else 1
# Independent expected processed stream: protocol escape syntax never reaches sinks.
TEXT=b'A\r\nB\x00\xff\x7fC\x1b[31mRED\x1b[0m\r\n'
PLAIN=b'A\r\nBCRED\r\n'
def recipes():
 return [dict(name='plain-native-filter-and-close'),dict(name='shutdown-closes-active',shutdown=True),dict(name='CR-adds-LF',crlf=True),dict(name='close-reopen-appends',reopen=True),dict(name='large-finite-queue',data=b'PRINTER0123456789'*32,expected=b'PRINTER0123456789'*32),dict(name='capture-active-independent',capture=True),dict(name='capture-held-independent',capture=True,hold=True),dict(name='raw-monitor-bypass',monitor=True),dict(name='unavailable-PRN-nonfatal',disabled=True)]
class PrinterPeer(MonitorPeer):
 def run(self):
  r=self.recipe
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();self.marker(b'm1');self.normal_text(r.get('data',TEXT));self.checks['processed_stream_answered_DSR']=True
    if r.get('monitor'):
     self.marker(b'm2');self.send(bytes(range(256)));self.marker(b'm3');self.normal_text(b'AFTERMONITOR\n')
    if r.get('reopen'):self.marker(b'm2');self.normal_text(b'SECOND\n')
    if r.get('shutdown'):
     while not self.stop.is_set():self.receive()
    self.marker(b'm4');self.normal_text(b'NOT PRINTED\n');self.marker(b'ready');self.normal_text(b'');self.checks['normal_parser_and_keyboard_after_close']=True
  except EOFError:
   if r.get('shutdown'):self.checks['actual_shutdown_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()
def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);rawfile=out/'PRINTER.RAW';peer=PrinterPeer(r);peer.thread.start()
 (out/'SNAP.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'SNAP.asm'),'-o',str(out/'SNAP.COM')],check=True)
 keys=['p1500']
 if r.get('capture'):
  keys+=['a-f1','p300']+list('D:\\CAP.LOG')+['enter','p300']
  if r.get('hold'):keys+=['a-f2','p300']
 if r.get('crlf'):keys+=['a-f3','p300']
 keys+=['a-l','p500','m','1','p1700']
 if r.get('monitor'):keys+=['c-\\','p300','n','p300','m','2','p1200','escape','p500','m','3','p1000']
 if r.get('reopen'):keys+=['a-l','p300','a-l','p300','m','2','p1000']
 if r.get('shutdown'):keys+=['a-x']
 else:
  keys+=['a-l','p500','m','4','p700']
  if r.get('capture'):keys+=['a-f1','p300']
  keys+=['r','e','a','d','y','p500','a-x']
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==1 else 'disabled') for i in range(1,5))
 parallel='disabled' if r.get('disabled') else f'file append:{rawfile}'
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[parallel]\nparallel1={parallel}\nparallel2=disabled\nparallel3=disabled\n[serial]\n{serial}\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nADDKEY {' '.join(keys)}\nC:\\TERMINAL COM1 38400 8N1 HARD\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nSNAP S\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(conf);started=time.monotonic();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 expected=r.get('expected',PLAIN)
 if r.get('crlf'):expected=expected.replace(b'\r',b'\r\n')
 if r.get('reopen'):expected+=b'SECOND\n'
 if r.get('monitor'):expected+=b'AFTERMONITOR\n'
 if r.get('disabled'):expected=b''
 checks=dict(peer.checks);checks.update(actual_ready=bool(peer.checks.get('actual_terminal_ready')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,no_peer_errors=not peer.errors,exact_virtual_PRN_bytes=read('PRINTER.RAW')==expected)
 if r.get('shutdown'):checks['required_actual_shutdown_closed_serial']=bool(peer.checks.get('actual_shutdown_closed_serial'))
 else:checks['required_postclose_parser_keyboard']=bool(peer.checks.get('normal_parser_and_keyboard_after_close'))
 if r.get('capture'):checks['independent_capture_bytes']=read('CAP.LOG')==(b'' if r.get('hold') else b'A\r\nBCRED\r\nNOT PRINTED\r\n') and (out/'CAP.LOG').exists()
 allowed={'SNAP.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','PRINTER.RAW'}|({'CAP.LOG'} if r.get('capture') else set());checks['no_unexpected_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 screen=read('SCREEN.BIN');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 (out/'expected-printer.bin').write_bytes(expected);(out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-started,3),keys=' '.join(keys),scope='ActualDOS PRN handle/IOCTL/write/close with DOSBox-X file-only virtualparallel. No physicalprinter/readinessstall/devicewritefault claim.');(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--probe',action='store_true');p.add_argument('--label',required=True);p.add_argument('--sha256');p.add_argument('--case',action='append',default=[]);a=p.parse_args();assert a.label.replace('-','').replace('_','').isalnum()
 if a.probe:return probe(a.label)
 assert a.sha256 and hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicit matching frozen runtime required';OUT.mkdir(exist_ok=True,parents=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in recipes() if not a.case or r['name'] in a.case]
 assert rows;result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
