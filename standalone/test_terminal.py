#!/usr/bin/env python3
"""Run the source-only live terminal through DOSBox-X UART and keyboard.

An independent generated DOS sampler records IRQ vectors/UART/PIC before and
following execution and captures actual text video memory without a product
/test flag. Network traffic stays on loopback.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/terminal/TERMINAL.EXE'
SAMPLER=r'''BITS 16
CPU 8086
ORG 0x100
start:
 cmp byte [0x82],'S'
 je screen
 mov dx,before_name
 cmp byte [0x82],'A'
 jne create
 mov dx,after_name
create:
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc failed
 mov bx,ax
 push ds
 xor ax,ax
 mov ds,ax
 mov dx,0x20
 mov cx,32
 mov ah,0x40
 int 0x21
 mov dx,0x70
 mov cx,4
 mov ah,0x40
 int 0x21
 pop ds
 ; Capture LCR, IER, MCR, divisor low/high, PIC mask atomically.
 pushf
 cli
 mov dx,0x3fb
 in al,dx
 mov [state],al
 and al,0x7f
 out dx,al
 mov dx,0x3f9
 in al,dx
 mov [state+1],al
 mov dx,0x3fc
 in al,dx
 mov [state+2],al
 mov dx,0x3fb
 mov al,[state]
 or al,0x80
 out dx,al
 mov dx,0x3f8
 in al,dx
 mov [state+3],al
 inc dx
 in al,dx
 mov [state+4],al
 mov dx,0x3fb
 mov al,[state]
 out dx,al
 in al,0x21
 mov [state+5],al
 popf
 mov dx,state
 mov cx,6
 mov ah,0x40
 int 0x21
 jmp close
screen:
 mov dx,screen_name
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc failed
 mov bx,ax
 push ds
 mov ax,0xb800
 mov ds,ax
 xor dx,dx
 mov cx,4000
 mov ah,0x40
 int 0x21
 pop ds
close:
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
before_name: db 'D:\BEFORE.BIN',0
after_name: db 'D:\AFTER.BIN',0
screen_name: db 'D:\SCREEN.BIN',0
state: times 6 db 0
'''


def run(case):
 output=ROOT/'build/terminal-tests'/case
 output.mkdir(parents=True,exist_ok=True)
 for name in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):
  (output/name).unlink(missing_ok=True)
 (output/'sampler.asm').write_text(SAMPLER)
 subprocess.run(['nasm','-f','bin',str(output/'sampler.asm'),'-o',str(output/'SNAP.COM')],check=True)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 checks={};events=[];times={};stop=threading.Event();wire=bytearray()
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(15)
 start=time.monotonic()

 def peer():
  try:
   connection,_=server.accept()
   with connection:
    connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);connection.settimeout(0.05)
    pending=bytearray()
    def receive_until(token,timeout=2):
     deadline=time.monotonic()+timeout
     while time.monotonic()<deadline and not stop.is_set():
      at=pending.find(token)
      if at>=0:
       del pending[:at+len(token)];return True
      try:
       data=connection.recv(4096)
       if not data:return False
       pending.extend(data);wire.extend(data)
      except socket.timeout:pass
      except (ConnectionResetError,BrokenPipeError):return False
     return False
    def collect(duration):
     deadline=time.monotonic()+duration
     while time.monotonic()<deadline and not stop.is_set():
      try:
       data=connection.recv(4096)
       if not data:break
       pending.extend(data);wire.extend(data)
      except socket.timeout:pass
      except (ConnectionResetError,BrokenPipeError):break
    # Serial connection predates program startup; DSR proves actual application
    # reception instead of assuming a fixed startup delay or adding a marker.
    time.sleep(0.2)
    ready=False
    for attempt in range(5):
     connection.sendall(b'\x1b[5n')
     if receive_until(b'\x1b[0n',0.4):ready=True;break
    checks['terminal_ready_via_actual_dsr']=ready
    if not ready:return
    times['ready_seconds']=round(time.monotonic()-start,3)
    if case=='normal':
     for fragment in [b'\x1b[2',b'J\x1b[HLo',b'C\r',b'\n\x1b[3',b'2mREADY\tOK',b'\x1b[0m\x1b[3;',b'5HSELECT\r\n']:
      connection.sendall(fragment);time.sleep(0.015)
     connection.sendall(b'\x1b[6n')
     checks['fragmented_menu_and_cursor_report']=receive_until(b'\x1b[4;1R')
     connection.sendall(b'\x1b[?1h')
     checks['application_cursor_up']=receive_until(b'\x1bOA',3)
     connection.sendall(b'\x1b[?1l')
     checks['normal_cursor_up']=receive_until(b'\x1b[A',3)
     checks['typed_ascii_q']=receive_until(b'q',2)
    elif case=='software':
     connection.sendall(b'FLOW WAIT\x13');times['stall_seconds']=round(time.monotonic()-start,3)
     collect(2)
     checks['xon_xoff_withholds_typed_q']=b'q' not in pending
    elif case=='partial':
     connection.sendall(b'PARTIAL\x1b[');times['partial_seconds']=round(time.monotonic()-start,3)
    elif case=='controller-disabled':
     # CSI5i is implemented; unavailable PRN must deny admission cleanly.
     connection.sendall(b'\x1b[5i');times['controller_disabled_seconds']=round(time.monotonic()-start,3)
    while not stop.wait(0.05):pass
  except (OSError,AssertionError) as error:events.append({'peer_error':str(error)})

 thread=threading.Thread(target=peer,daemon=True);thread.start()
 keyboard={'normal':'p1800 up p1500 up p800 q p1000 a-x','software':'p1000 q p1000 a-x','partial':'p1000 a-x','controller-disabled':'p3000 a-x'}[case]
 arguments=' SOFT' if case=='software' else ''
 branch='if errorlevel 1 goto failed\ngoto expected'
 config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[parallel]
parallel1=disabled
parallel2=disabled
parallel3=disabled
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{BINARY.parent}"
mount d "{output}"
c:
D:\\SNAP B
ADDKEY {keyboard}
TERMINAL{arguments}
{branch}
:expected
D:\\SNAP S
D:\\SNAP A
echo PASS>D:\\PASS.TXT
goto done
:failed
D:\\SNAP S
D:\\SNAP A
echo FAIL>D:\\FAIL.TXT
:done
exit
'''
 (output/'dosbox.conf').write_text(config)
 env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
 with (output/'dosbox.log').open('w') as log:
  process=subprocess.Popen(['dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf')],cwd=output,env=env,stdout=log,stderr=log)
  try:code=process.wait(timeout=15)
  except subprocess.TimeoutExpired:
   process.terminate()
   try:process.wait(timeout=2)
   except subprocess.TimeoutExpired:process.kill();process.wait()
   code=-1
 elapsed=time.monotonic()-start;stop.set();server.close();thread.join(timeout=2)
 (output/'serial-received.bin').write_bytes(wire)
 checks['expected_dos_exit_and_capture']=code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists()
 before=(output/'BEFORE.BIN').read_bytes() if (output/'BEFORE.BIN').exists() else b''
 after=(output/'AFTER.BIN').read_bytes() if (output/'AFTER.BIN').exists() else b''
 checks['hardware_irq_vectors_restored']=len(before)==42 and len(after)==42 and before[:36]==after[:36]
 checks['uart_and_pic_restored']=len(before)==42 and len(after)==42 and before[36:]==after[36:]
 if before and after:events.append({'before_hardware':before[36:].hex(),'after_hardware':after[36:].hex()})
 screen=(output/'SCREEN.BIN').read_bytes() if (output/'SCREEN.BIN').exists() else b''
 checks['screen_captured']=len(screen)==4000
 if len(screen)==4000:
  (output/'screen.txt').write_text('\n'.join(bytes(screen[row*160:row*160+160:2]).decode('cp437') for row in range(25))+'\n')
  if case=='normal':
   def cells(row,column,text,attribute):
    at=row*160+column*2
    return screen[at:at+len(text)*2]==b''.join(bytes([value,attribute]) for value in text)
   checks['actual_video_menu_text_and_sgr']=cells(0,0,b'LoC',7) and cells(1,0,b'READY',2) and cells(1,8,b'OK',2) and cells(2,4,b'SELECT',7)
 if case=='partial':checks['alt_x_interrupts_partial_escape_before_parser_deadline']=elapsed-times.get('partial_seconds',0)<1.8
 if case=='software':checks['alt_x_exits_while_transmit_paused']=elapsed<3.5
 required=['terminal_ready_via_actual_dsr','expected_dos_exit_and_capture','hardware_irq_vectors_restored','uart_and_pic_restored','screen_captured']
 required+= {'normal':['fragmented_menu_and_cursor_report','application_cursor_up','normal_cursor_up','typed_ascii_q','actual_video_menu_text_and_sgr'],'software':['xon_xoff_withholds_typed_q','alt_x_exits_while_transmit_paused'],'partial':['alt_x_interrupts_partial_escape_before_parser_deadline'],'controller-disabled':[]}[case]
 result={'case':case,'passed':all(checks.get(key,False) for key in required),'checks':checks,'seconds':round(elapsed,3),'timing':times,'events':events,'binary_sha256':digest,'received_hex':wire.hex(),'scope':'Source-only DOS terminal, actual emulated UART/PIC/keyboard/BIOS video and private loopback TCP peer; independent DOS hardware/vector/video sampler. No original PCPlus executable or public BBS.'}
 (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
 return result['passed']


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--case',choices=['normal','software','partial','controller-disabled','all'],default='all')
 args=parser.parse_args()
 directory=ROOT/'build/terminal-tests';directory.mkdir(parents=True,exist_ok=True)
 with (directory/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  cases=['normal','software','partial','controller-disabled'] if args.case=='all' else [args.case]
  results=[run(case) for case in cases]
 return 0 if all(results) else 1
if __name__=='__main__':raise SystemExit(main())
