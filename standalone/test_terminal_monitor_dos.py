#!/usr/bin/env python3
"""Independent actualDOS rawmonitor: real BIOS/UART/files and liveB800 observer.

Sourcebuilt temporary INT16 observer chains real BIOS reads, samples on digit2,
then verifies/restores original vectors. No product callbacks or replies mocked.
All media synthetic/owned; explicit runtime freeze and fresh labels required.
"""
import argparse,fcntl,hashlib,json,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as TerminalPeer
from test_terminal_capture_dos import DUMP as TRACE_DUMP,INSTALL as TRACE_INSTALL,audit_kernel_trace
from terminal_config_fixtures import image as config_image,RATES
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';OUT=ROOT/'build/terminal-monitor-dos'
RAW=bytes(range(256));SEED=b'OLD DUMP\x1aMUST BE REPLACED\r\n';AFTER=b'\x1b[2J\x1b[HNORMAL PARSER RESUMED\r\n\x1b[31mRED\x1b[0m\n';AFTER_LOG=b'NORMAL PARSER RESUMED\r\nRED\r\n'
OBSERVER=r'''
bits 16
org 100h
jmp install
old16 dd 0
old2f dd 0
state:
 dw 0xc53a,1,0,0
saved16 dd 0
saved2f dd 0
 dw hook16,hook2f
 dw 0,0,0,0
screen times 4000 db 0
hook16:
 pushf
 cmp ah,0
 je .read
 cmp ah,0x10
 je .read
 popf
 jmp far [cs:old16]
.read:
 popf
 pushf
 call far [cs:old16]
 pushf
 cmp al,'2'
 jne .return
 cmp word [cs:state+4],0
 jne .return
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov word [cs:state+4],1
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [cs:state+20],ax
 mov ax,[es:0x60]
 mov [cs:state+22],ax
 mov al,[es:0x49]
 mov ah,[es:0x4a]
 mov [cs:state+24],ax
 xor ax,ax
 mov al,[es:0x62]
 mov [cs:state+26],ax
 mov ax,0xb800
 mov ds,ax
 push cs
 pop es
 xor si,si
 mov di,screen
 mov cx,2000
 cld
 rep movsw
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
.return:
 popf
 iret
hook2f:
 pushf
 cmp ax,0xd7c3
 jne .chain
 cmp bx,0x4d4f
 jne .chain
 popf
 mov ax,0xc53a
 push cs
 pop es
 mov di,state
 iret
.chain:
 popf
 jmp far [cs:old2f]
install:
 mov ax,0xd7c3
 mov bx,0x4d4f
 int 0x2f
 cmp ax,0xc53a
 je .fail
 mov ax,0x3516
 int 0x21
 mov [old16],bx
 mov [saved16],bx
 mov [old16+2],es
 mov [saved16+2],es
 mov ax,0x352f
 int 0x21
 mov [old2f],bx
 mov [saved2f],bx
 mov [old2f+2],es
 mov [saved2f+2],es
 mov dx,hook16
 mov ax,0x2516
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
OBSERVER_DUMP=TRACE_DUMP.replace('0xd7c1','0xd7c3').replace('0x4c43','0x4d4f').replace('0xc51a','0xc53a').replace('0x3521','0x3516').replace('0x2521','0x2516').replace('660','4028').replace('666','4034').replace("'CT21'","'MV16'").replace("'TRACE.BIN'","'MONVIEW.BIN'")
def recipes():
 return [dict(name='all256-Y-replace',choice='y',seed=SEED),dict(name='all256-N-no-log',choice='n',seed=SEED),dict(name='all256-N-no-create',choice='n'),dict(name='all256-Enter-no-log',choice='enter',seed=SEED),dict(name='all256-Esc-no-log',choice='escape',seed=SEED),dict(name='raw-over256-buffer',choice='y',data=RAW+RAW+b'BINARY\x00\xff'),dict(name='periodic-raw-flush',choice='y',data=b'RAW\x00\x1b\xffPERIOD',periodic=True),dict(name='keyboard-bindings-owner-denials',choice='y',keyboard=True),dict(name='capture-active-bypass-and-resume',choice='y',capture=True),dict(name='capture-held-bypass-and-resume',choice='y',capture=True,hold=True),dict(name='capture-active-DMP-conflict',choice='y',capture=True,conflict=True),dict(name='capture-held-DMP-conflict',choice='y',capture=True,hold=True,conflict=True),dict(name='readonly-DMP-denied-view-only',choice='y',seed=SEED,readonly=True),dict(name='AltX-closes-active-monitor',choice='y',exit=True),dict(name='explicit-PRM-all256',choice='y',prm=True)]
class MonitorPeer(TerminalPeer):
 def __init__(self,recipe):self.markers=[];super().__init__(recipe)
 def marker(self,value):
  deadline=time.monotonic()+25
  while time.monotonic()<deadline and not self.stop.is_set():
   at=bytes(self.pending).find(value)
   if at>=0:
    consumed=bytes(self.pending[:at+len(value)]);del self.pending[:at+len(value)];self.markers.append(consumed);self.log('actual-BIOS-marker',hex=value.hex(),consumed=consumed.hex());return consumed
   self.receive()
  raise TimeoutError('Missing actual BIOS marker '+repr(value))
 def normal_text(self,text):
  self.send(text+b'\x1b[5n');deadline=time.monotonic()+6
  while time.monotonic()<deadline and not self.stop.is_set():
   at=bytes(self.pending).find(b'\x1b[0n')
   if at>=0:del self.pending[:at+4];self.checks['actual_normal_parser_DSR']=True;return
   self.receive()
  raise TimeoutError('Normal parser DSR missing')
 def run(self):
  r=self.recipe
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready()
    if r.get('capture'):self.marker(b'm0');self.normal_text(b'BEFORE\n')
    self.marker(b'm1');self.send(r.get('data',RAW));self.log('sent-raw-monitor-bytes',size=len(r.get('data',RAW)))
    got=self.marker(b'm2');self.checks['no_ANSI_or_control_responses_during_monitor']=got==(b'hello\x1b[Am2' if r.get('keyboard') else b'm2')
    if r.get('exit'):
     while not self.stop.is_set():self.receive()
    self.marker(b'm3');self.normal_text(AFTER);self.marker(b'ready');self.normal_text(b'');self.checks['actual_normal_keyboard_after_exit']=True
  except EOFError:
   if r.get('exit'):self.checks['actual_AltX_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()
def audit_view(output,data,normal=7,special=15):
 raw=(output/'MONVIEW.BIN').read_bytes() if (output/'MONVIEW.BIN').exists() else b''
 ok=len(raw)==4034 and raw[:4]==b'MV16' and raw[4:6]==b'\x0f\x00' and raw[6:14]==b'\x3a\xc5\x01\x00\x01\x00\x00\x00'
 expected=bytes(48 if c==0 else 63 if c==255 else c for c in data)
 attrs=bytes(special if c in (0,27,255) else normal for c in data);view=raw[34:]
 result=dict(passed=bool(ok and view[:len(data)*2:2]==expected and view[1:len(data)*2:2]==attrs),observer_chain_verified_restored=ok,actual_chars_hex=view[:len(data)*2:2].hex(),expected_chars_hex=expected.hex(),actual_attrs_hex=view[1:len(data)*2:2].hex(),expected_attrs_hex=attrs.hex(),scope='Independent realBIOSread observer capturesB800 on digit2 before Escape clearsmonitor; hooks16/2F chainchecked andrestored. Prefixcells only; transientbottomnotices excluded.')
 (output/'view-oracle.json').write_text(json.dumps(result,indent=2)+'\n');return result

def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);dump=out/'PCPLUS.DMP';data=r.get('data',RAW)
 if r.get('seed') is not None:dump.write_bytes(r['seed'])
 if r.get('readonly'):dump.chmod(0o444)
 sources=[('MONOBS',OBSERVER),('MONDUMP',OBSERVER_DUMP)]
 if r.get('periodic'):sources=[('TRCINST',TRACE_INSTALL),('TRCDUMP',TRACE_DUMP)]+sources
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[a.com-1]
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(base+off))
 for stem,source in sources+[('SNAP',sampler)]:
  (out/(stem+'.asm')).write_text(source);subprocess.run(['nasm','-fbin',str(out/(stem+'.asm')),'-o',str(out/(stem+'.COM'))],check=True)
 peer=MonitorPeer(r);peer.thread.start();keys=['p1500']
 if r.get('capture'):
  keys+=['a-f1','p300']+list('D:\\PCPLUS.DMP' if r.get('conflict') else 'D:\\CAP.LOG')+['enter','p300']
  if r.get('hold'):keys+=['a-f2','p300']
  keys+=['m','0','p700']
 keys+=['c-\\','p300',r['choice'],'p500','m','1','p2500' if r.get('periodic') else 'p1700']
 if r.get('keyboard'):keys+=['c-\\','a-r','a-s','a-f1','a-f4','a-g','a-1','h','e','l','l','o','up']
 keys+=['m','2','p500']
 if r.get('exit'):keys+=['a-x']
 else:
  keys+=['escape','p500','m','3','p700']
  if r.get('capture'):keys+=['a-f1','p500']
  keys+=['r','e','a','d','y','p500','a-x']
 command=f'C:\\TERMINAL COM{a.com} {a.baud} 8N1 {a.flow}';prm=None
 if r.get('prm'):
  prm=config_image(port=a.com,baud=RATES.index(a.baud),soft=0,hard=int(a.flow=='HARD'),normal=7);(out/'TEST.PRM').write_bytes(prm);command='C:\\TERMINAL @D:\\TEST.PRM'
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==a.com else 'disabled') for i in range(1,5));install=('TRCINST\nif errorlevel 1 goto fail\n' if r.get('periodic') else '')+'MONOBS\nif errorlevel 1 goto fail\n'
 finish='MONDUMP\nif errorlevel 1 goto observerfail\n'+('TRCDUMP\nif errorlevel 1 goto observerfail\n' if r.get('periodic') else '')+'goto observed\n:observerfail\necho FAIL>OBSFAIL.TXT\n:observed\n'
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\n{serial}\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\n{install}SNAP B\nADDKEY {' '.join(keys)}\n{command}\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto capture\n:fail\necho FAIL>FAIL.TXT\n:capture\nSNAP S\nSNAP A\n{finish}exit\n'''
 (out/'dosbox.conf').write_text(conf);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256;start=time.monotonic()
 with (out/'dosbox.log').open('w') as f:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=f,stderr=f,timeout=a.timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 checks=dict(peer.checks);checks.update(actual_initial_DSR=bool(checks.get('actual_terminal_ready')),actual_literal_forward_and_no_interpreter=bool(checks.get('no_ANSI_or_control_responses_during_monitor')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),runtime_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,no_peer_errors=not peer.errors,observer_completed=not (out/'OBSFAIL.TXT').exists())
 checks['actual_raw_display_chars_and_attrs']=audit_view(out,data,special=0x2f if r.get('prm') else 15)['passed']
 expected_capture=b'' if r.get('hold') else b'BEFORE\r\n'+AFTER_LOG
 if r.get('conflict'):expected=expected_capture
 elif r.get('readonly') or r['choice']!='y':expected=r.get('seed')
 else:expected=data
 checks['exact_DMP_replacement_or_preservation']=dump.exists() and dump.read_bytes()==expected if expected is not None else not dump.exists()
 if r.get('capture') and not r.get('conflict'):checks['capture_bypassed_raw_and_state_preserved']=read('CAP.LOG')==expected_capture and (out/'CAP.LOG').exists()
 if r.get('readonly'):checks['readonly_mode_preserved']=dump.stat().st_mode&0o222==0
 if r.get('prm'):checks['synthetic_PRM_unchanged']=read('TEST.PRM')==prm
 if r.get('periodic'):checks['actual_periodic_DOS_write_before_close']=audit_kernel_trace(out,len(data))['passed']
 if r.get('exit'):checks['required_AltX_closed_serial']=bool(checks.get('actual_AltX_closed_serial'))
 else:checks['required_normal_parser_keyboard_resume']=bool(checks.get('actual_normal_parser_DSR') and checks.get('actual_normal_keyboard_after_exit'));checks['normal_ANSI_video_resume']=len(read('SCREEN.BIN'))==4000 and read('SCREEN.BIN')[:42:2]==b'NORMAL PARSER RESUMED'
 allowed={'MONOBS.asm','MONOBS.COM','MONDUMP.asm','MONDUMP.COM','SNAP.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','MONVIEW.BIN','view-oracle.json','PCPLUS.DMP'}|({'CAP.LOG'} if r.get('capture') and not r.get('conflict') else set())|({'TEST.PRM'} if r.get('prm') else set())|({'TRCINST.asm','TRCINST.COM','TRCDUMP.asm','TRCDUMP.COM','TRACE.BIN','kernel-trace.json'} if r.get('periodic') else set());checks['no_unexpected_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');screen=read('SCREEN.BIN');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-start,3),command=command,keys=' '.join(keys),raw_size=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),scope='ActualDOS rawmonitor/BIOS/UART/renderer/DOSowners, independentallbytewireoracle andrealINT16B800observer withverified/restoredchain. No physicalserialhardware,softwareflowall-byteclaim,filesystemwritefault ornativeHOOK execution.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def self_check():
 assert len(RAW)==256 and len(set(RAW))==256
 assert bytes(48 if c==0 else 63 if c==255 else c for c in RAW)[27]==27
 assert len(OBSERVER_DUMP)>1000 and '0x3516' in OBSERVER_DUMP and "'MV16'" in OBSERVER_DUMP
 from tempfile import TemporaryDirectory
 with TemporaryDirectory() as tmp:
  folder=Path(tmp);raw=bytearray(4034);raw[:14]=b'MV16\x0f\x00\x3a\xc5\x01\x00\x01\x00\x00\x00'
  for i,c in enumerate(RAW):raw[34+2*i]=48 if c==0 else 63 if c==255 else c;raw[35+2*i]=0x2f if c in (0,27,255) else 7
  (folder/'MONVIEW.BIN').write_bytes(raw)
  assert audit_view(folder,RAW,special=0x2f)['passed']
  assert not audit_view(folder,RAW)['passed']
 print('Rawmonitor fixture/oracle self-check passed; no terminal runtime executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--baud',type=int,choices=RATES,default=38400);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--timeout',type=int,default=90);a=p.parse_args();assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256;OUT.mkdir(parents=True,exist_ok=True);selected=[r for r in recipes() if not a.case or r['name'] in a.case];assert selected
 with (OUT/'.lock').open('w') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,a) for r in selected]
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
