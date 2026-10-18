#!/usr/bin/env python3
"""Independent actualDOS processed-text capture tests on fresh synthetic media.

Real BIOS AltF1/F2/F3, UART and DOS files; no mocked product callbacks/replies.
Protocol peer sends test text/queries and observes actual DOS marker keys/DSR.
Requires an explicit frozen runtime hash, never touches a mounted DOS drive.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as TerminalPeer,frame,payload
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';OUT=ROOT/'build/terminal-capture-dos'
TEXT=b'\x1b[2J\x1b[HCAPTURE READY\r\n\x1b[31mRED\x1b[0m! \x7f\xff\rTAIL\n'
NORMAL=b'CAPTURE READY\r\nRED! TAIL\r\n';SEED=b'OLD\x1aSTILL HERE\r\n'
INSTALL=r'''
bits 16
org 100h
jmp install
old21 dd 0
old2f dd 0
state:
 dw 0xc51a,1,0,0
saved21 dd 0
saved2f dd 0
 dw hook21,hook2f
records times 640 db 0
hook21:
 pushf
 cmp ah,0x40
 je .record
 cmp ah,0x3e
 jne .chain
.record:
 push bp
 mov bp,sp
 push ax
 push bx
 push cx
 push dx
 push di
 push es
 mov di,[cs:state+4]
 cmp di,64
 jb .space
 mov word [cs:state+6],1
 jmp .done
.space:
 shl di,1
 mov ax,di
 shl di,1
 shl di,1
 add di,ax
 mov ax,[ss:bp-2]
 mov [cs:records+di],ax
 mov ax,[ss:bp-4]
 mov [cs:records+di+2],ax
 mov ax,[ss:bp-6]
 mov [cs:records+di+4],ax
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov [cs:records+di+6],ax
 mov ax,[es:0x6e]
 mov [cs:records+di+8],ax
 inc word [cs:state+4]
.done:
 pop es
 pop di
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
.chain:
 popf
 jmp far [cs:old21]
hook2f:
 pushf
 cmp ax,0xd7c1
 jne .chain
 cmp bx,0x4c43
 jne .chain
 popf
 mov ax,0xc51a
 push cs
 pop es
 mov di,state
 iret
.chain:
 popf
 jmp far [cs:old2f]
install:
 mov ax,0xd7c1
 mov bx,0x4c43
 int 0x2f
 cmp ax,0xc51a
 je .fail
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [saved21],bx
 mov [old21+2],es
 mov [saved21+2],es
 mov ax,0x352f
 int 0x21
 mov [old2f],bx
 mov [saved2f],bx
 mov [old2f+2],es
 mov [saved2f+2],es
 mov dx,hook21
 mov ax,0x2521
 int 0x21
 mov dx,hook2f
 mov ax,0x252f
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
resident_end:
'''
DUMP=r'''
bits 16
org 100h
 mov ax,0xd7c1
 mov bx,0x4c43
 int 0x2f
 cmp ax,0xc51a
 jne fail
 cmp word [es:di],0xc51a
 jne fail
 mov [tsr],es
 mov si,di
 push ds
 push es
 pop ds
 pop es
 mov di,buffer
 mov cx,660
 rep movsb
 push es
 pop ds
 cmp word [buffer+4],64
 ja fail
 mov ax,0x3521
 int 0x21
 mov ax,es
 cmp ax,[tsr]
 jne fail
 cmp bx,[buffer+16]
 jne fail
 or word [verified],1
 mov ax,0x352f
 int 0x21
 mov ax,es
 cmp ax,[tsr]
 jne fail
 cmp bx,[buffer+18]
 jne fail
 or word [verified],2
 push ds
 mov dx,[buffer+8]
 mov ax,[buffer+10]
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 push ds
 mov dx,[buffer+12]
 mov ax,[buffer+14]
 mov ds,ax
 mov ax,0x252f
 int 0x21
 pop ds
 mov ax,0x3521
 int 0x21
 mov ax,es
 cmp ax,[buffer+10]
 jne fail
 cmp bx,[buffer+8]
 jne fail
 or word [verified],4
 mov ax,0x352f
 int 0x21
 mov ax,es
 cmp ax,[buffer+14]
 jne fail
 cmp bx,[buffer+12]
 jne fail
 or word [verified],8
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc fail
 mov bx,ax
 mov dx,report
 mov cx,666
 mov ah,0x40
 int 0x21
 jc fail
 cmp ax,666
 jne fail
 mov ah,0x3e
 int 0x21
 jc fail
 mov ax,0x4c00
 int 0x21
fail:
 mov ax,0x4c01
 int 0x21
tsr dw 0
filename db 'TRACE.BIN',0
report db 'CT21'
verified dw 0
buffer times 660 db 0
'''

def keytext(value):return list(value)
def openkeys(name=None):return ['a-f1','p300']+(keytext(name) if name else [])+['enter']
def marker(number):return ['p500','m',str(number)]
def recipes():
 return [
 dict(name='escape-no-create',cancel=True,keys=['a-f1','p300','escape']+marker(1),phases=[dict(marker=b'm1',text=TEXT)],expected=None),
 dict(name='default-filename',keys=openkeys()+marker(1)+['p1500','a-f1'],phases=[dict(marker=b'm1',text=TEXT)],expected=NORMAL,filename='PCPLUS.LOG'),
 dict(name='explicit-filename',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1500','a-f1'],phases=[dict(marker=b'm1',text=TEXT)],expected=NORMAL),
 dict(name='repeat-append-DOS1A',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1200','a-f1','p500']+openkeys('D:\\LOG.TXT')+marker(2)+['p1200','a-f1'],phases=[dict(marker=b'm1',text=b'FIRST\n'),dict(marker=b'm2',text=b'SECOND\n')],seed=SEED,expected=SEED+b'FIRST\r\nSECOND\r\n'),
 dict(name='pause-resume',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1200','a-f2']+marker(2)+['p1200','a-f2']+marker(3)+['p1200','a-f1'],phases=[dict(marker=b'm1',text=b'FIRST\n'),dict(marker=b'm2',text=b'PAUSED MUST NOT LOG\n'),dict(marker=b'm3',text=b'SECOND\n')],expected=b'FIRST\r\nSECOND\r\n'),
 dict(name='CR-adds-LF-toggle',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1200','a-f3']+marker(2)+['p1200','a-f3']+marker(3)+['p1200','a-f1'],phases=[dict(marker=b'm1',text=b'A\rB\n'),dict(marker=b'm2',text=b'C\rD\r\n'),dict(marker=b'm3',text=b'E\rF\n')],expected=b'AB\r\nC\r\nD\r\n\r\nEF\r\n'),
 dict(name='periodic-flush',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p2500','a-f1'],phases=[dict(marker=b'm1',text=b'PERIODIC\n',periodic=True)],expected=b'PERIODIC\r\n'),
 dict(name='shutdown-flush',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p300'],phases=[dict(marker=b'm1',text=b'SHUTDOWN\n')],expected=b'SHUTDOWN\r\n',shutdown=True),
 dict(name='buffer-over256',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1500','a-f1'],phases=[dict(marker=b'm1',text=b'L'*777+b'\n')],expected=b'L'*777+b'\r\n'),
 dict(name='readonly-open-failure',keys=openkeys('D:\\LOCK.LOG')+marker(1),phases=[dict(marker=b'm1',text=TEXT)],filename='LOCK.LOG',seed=SEED,expected=SEED,readonly=True),
 dict(name='capture-XMODEM-coexistence',keys=openkeys('D:\\LOG.TXT')+marker(1)+['p1000','a-r','p300']+keytext('D:\\RECV.BIN')+['enter','p3500']+marker(2)+['p1000','a-f1'],phases=[dict(marker=b'm1',text=b'BEFORE\n'),dict(transfer=True),dict(marker=b'm2',text=b'AFTER\n')],expected=b'BEFORE\r\nAFTER\r\n',transfer=True),
 ]
class CapturePeer(TerminalPeer):
 def __init__(self,recipe,output):self.output=output;self.observations={};super().__init__(recipe)
 def wait_marker(self,want,timeout=20):
  end=time.monotonic()+timeout
  while time.monotonic()<end and not self.stop.is_set():
   at=bytes(self.pending).find(want)
   if at>=0:del self.pending[:at+len(want)];self.log('actual-BIOS-marker',text=want.decode());return
   self.receive()
  raise TimeoutError('No actual DOS marker '+repr(want))
 def text(self,data):
  self.send(data+b'\x1b[5n');self.log('sent-text-and-DSR',size=len(data),sha256=hashlib.sha256(data).hexdigest())
  end=time.monotonic()+5
  while time.monotonic()<end and not self.stop.is_set():
   at=bytes(self.pending).find(b'\x1b[0n')
   if at>=0:del self.pending[:at+4];self.checks['actual_DSR_after_each_text']=True;return
   self.receive()
  raise TimeoutError('No actual DSR after capture text')
 def transfer(self):
  self.control({67},15);data=payload(128);self.send(frame(data,1));self.control({6});self.send(b'\x04');self.control({21});self.send(b'\x04');self.control({6})
  target=self.output/'RECV.BIN';assert target.exists() and target.read_bytes()==data,'XMODEM exact file before ACK';self.checks['actual_XMODEM_transfer']=True
 def run(self):
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready()
    for phase in self.recipe['phases']:
     if phase.get('transfer'):self.transfer();continue
     self.wait_marker(phase['marker']);self.text(phase['text'])
     if phase.get('periodic'):
      path=self.output/self.recipe.get('filename','LOG.TXT');end=time.monotonic()+1.8
      while time.monotonic()<end and (not path.exists() or path.read_bytes()!=self.recipe['expected']):time.sleep(.03)
      self.observations['host_periodic_visibility_before_stop']=path.exists() and path.read_bytes()==self.recipe['expected']
      self.log('periodic-flush-observation',passed=self.observations['host_periodic_visibility_before_stop'])
    if self.recipe.get('shutdown'):
     self.checks['shutdown_text_DSR_before_exit']=True
     while not self.stop.is_set():self.receive()
    else:
     self.wait_marker(b'ready',20);self.checks['actual_postcapture_keyboard']=True
     self.text(b'');self.checks['actual_postcapture_DSR']=True
  except EOFError:
   if self.recipe.get('shutdown'):self.checks['actual_shutdown_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()

def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);filename=r.get('filename','LOG.TXT');logpath=out/filename
 if r.get('seed') is not None:logpath.write_bytes(r['seed'])
 if r.get('readonly'):logpath.chmod(0o444)
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[a.com-1]
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 if r['name']=='periodic-flush':
  for stem,source in [('TRCINST',INSTALL),('TRCDUMP',DUMP)]:
   (out/(stem+'.asm')).write_text(source);subprocess.run(['nasm','-fbin',str(out/(stem+'.asm')),'-o',str(out/(stem+'.COM'))],check=True)
 peer=CapturePeer(r,out);peer.thread.start();keys=['p1500']+r['keys']+([] if r.get('shutdown') else ['p500','r','e','a','d','y','p500'])+['a-x']
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==a.com else 'disabled') for i in range(1,5))
 command=f'C:\\TERMINAL COM{a.com} {a.baud} 8N1 {a.flow}';error=r.get('error',0)
 exit_check='if errorlevel 1 goto fail' if not error else 'if errorlevel 13 goto fail\nif not errorlevel 12 goto fail'
 trace_install='TRCINST\nif errorlevel 1 goto fail\n' if r['name']=='periodic-flush' else ''
 trace_dump='TRCDUMP\nif errorlevel 1 goto tracefail\ngoto tracedone\n:tracefail\necho FAIL>TRACEERR.TXT\n:tracedone\n' if r['name']=='periodic-flush' else ''
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\n{serial}\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\n{trace_install}SNAP B\nADDKEY {' '.join(keys)}\n{command}\n{exit_check}\necho PASS>PASS.TXT\ngoto capture\n:fail\necho FAIL>FAIL.TXT\n:capture\nSNAP S\nSNAP A\n{trace_dump}exit\n'''
 (out/'dosbox.conf').write_text(conf);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime changed';start=time.monotonic()
 with (out/'dosbox.log').open('w') as f:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=f,stderr=f,timeout=a.timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 checks=dict(peer.checks);checks['DOS_video_captured']=len(read('SCREEN.BIN'))==4000;checks.update(actual_initial_DSR=bool(checks.get('actual_terminal_ready')),actual_DSR_for_each_phase=bool(checks.get('actual_DSR_after_each_text')),no_peer_errors=not peer.errors,DOS_expected_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256)
 if r.get('shutdown'):checks['required_actual_shutdown']=bool(checks.get('actual_shutdown_closed_serial'))
 else:checks['required_actual_keyboard_and_DSR']=bool(checks.get('actual_postcapture_keyboard') and checks.get('actual_postcapture_DSR'))
 if r['expected'] is None:checks['escape_no_files_created']=not logpath.exists() and not (out/'PCPLUS.LOG').exists()
 else:checks['exact_processed_log_bytes']=logpath.exists() and logpath.read_bytes()==r['expected']
 if r['name']=='periodic-flush':
  trace=audit_kernel_trace(out,len(r['expected']));checks['actual_kernel_periodic_write_before_close']=trace['passed']
 allowed={'sampler.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'}|({filename} if r['expected'] is not None else set())|({'RECV.BIN'} if r.get('transfer') else set())
 if r['name']=='periodic-flush':allowed|={'TRCINST.asm','TRCDUMP.asm','TRCINST.COM','TRCDUMP.COM','TRACE.BIN','kernel-trace.json'}
 checks['no_other_created_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 if r.get('readonly'):checks['readonly_preserved']=logpath.stat().st_mode&0o222==0
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');screen=read('SCREEN.BIN');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,observations=peer.observations,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-start,3),command=command,keys=' '.join(keys),expected_capture_hex=None if r['expected'] is None else r['expected'].hex(),actual_capture_hex=logpath.read_bytes().hex() if logpath.exists() else None,scope='Actual DOS processed-text capture/UI/hotkeys/UART/files and hardware snapshots. Independent controlled serial text/queries; no generated DOS replies, rawwirecapture or physical timing claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def audit_kernel_trace(output,expected_count):
 raw=(output/'TRACE.BIN').read_bytes() if (output/'TRACE.BIN').exists() else b''
 valid=len(raw)==666 and raw[:4]==b'CT21' and int.from_bytes(raw[4:6],'little')==15
 records=[];early=[];count=overflow=0
 if valid:
  data=raw[6:];count=int.from_bytes(data[4:6],'little');overflow=int.from_bytes(data[6:8],'little')
  valid=data[:4]==b'\x1a\xc5\x01\x00' and count<=64 and overflow==0
  for i in range(min(count,64)):
   row=data[20+i*10:30+i*10];words=[int.from_bytes(row[n:n+2],'little') for n in range(0,10,2)]
   records.append(dict(function=words[0]>>8,handle=words[1],count=words[2],ticks=words[3]|words[4]<<16))
  for i,row in enumerate(records):
   if row['function']!=0x40 or row['handle']<5 or row['count']!=expected_count:continue
   close=next((r for r in records[i+1:] if r['function']==0x3e and r['handle']==row['handle']),None)
   if close:
    delta=(close['ticks']-row['ticks'])%0x1800b0
    if 10<=delta<100:early.append(dict(write_index=i,close_delta_ticks=delta))
 result=dict(passed=bool(valid and early and not (output/'TRACEERR.TXT').exists()),chain_signature_and_restoration_checked=valid,overflow=overflow,records=records,early_writes=early,scope='Independent source-built temporary INT21 trace, no product callback changes. Records actualAH40/AH3E and BIOS ticks; full vectorchain verified before and after restoration. At least10 ticks beforeclose proves earlyDOSwrite, not hoststdio visibility or exact18tick timing.')
 (output/'kernel-trace.json').write_text(json.dumps(result,indent=2)+'\n');return result

def self_check():
 assert len({r['name'] for r in recipes()})==len(recipes())
 assert all('period' not in r['keys'] for r in recipes())
 assert b'\x1a' in SEED and NORMAL==b'CAPTURE READY\r\nRED! TAIL\r\n'
 print('Capture recipe/oracle self-check passed; no terminal runtime executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--baud',type=int,default=38400);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--timeout',type=int,default=80);a=p.parse_args()
 assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicit frozen binary required';OUT.mkdir(parents=True,exist_ok=True)
 selected=[r for r in recipes() if not a.case or r['name'] in a.case];assert selected
 with (OUT/'.lock').open('w') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in selected]
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
