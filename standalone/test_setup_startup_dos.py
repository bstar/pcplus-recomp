#!/usr/bin/env python3
"""Setup child before UART ownership, then real PRM import and terminal I/O."""
import hashlib,json,os,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from test_terminal import SAMPLER
from check_setup_model import image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup-startup';BINARY=ROOT/'build/terminal/TERMINAL.EXE';EDITOR=ROOT/'build/setup/PRMEDIT.EXE'
def probe_child():
 # Independently sample the UART/vector/PIC at child ENTRY and its exact PSP
 # command tail. Source-built MZ; no vendor child or private settings involved.
 prelude='''start:
 mov ax,cs
 mov ds,ax
 mov dx,tail_name
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc failed
 mov bx,ax
 push ds
 push es
 pop ds
 mov dx,0x80
 mov cx,128
 mov ah,0x40
 int 0x21
 pop ds
 mov ah,0x3e
 int 0x21
 mov dx,before_name
'''
 source=SAMPLER.replace('ORG 0x100','SEGMENT _TEXT public class=CODE use16\n..start:')
 source=source[:source.index('start:')]+prelude+source[source.index('create:'):]
 source=source.replace('D:\\BEFORE.BIN','D:\\CHILDHW.BIN')
 source+="\ntail_name: db 'D:\\CHILDARG.BIN',0\nSEGMENT STACK stack class=STACK use16\n resb 1024\n"
 (OUT/'probe.asm').write_text(source)
 subprocess.run(['nasm','-f','obj',str(OUT/'probe.asm'),'-o',str(OUT/'probe.obj')],check=True)
 subprocess.run(['wlink','system','dos','option','quiet','name',str(OUT/'PROBE.EXE'),'file',str(OUT/'probe.obj')],check=True)
 return (OUT/'PROBE.EXE').read_bytes()
def run(name,*,keys='',child='editor',payload=None,arguments='/S @TEST.PRM',rate=1200,expected=0,ready=True,post_echo=False,rate_mask=None,line_mask=None,expected_profile=None,profile_clear=False,keyboard_file=None,files=None,environment=None,child_binary=None,post_banner=None,expected_files=None,pause_after_input=None,cpu='386'):
 assert cpu in ('386','8086')
 assert set(expected_files or {})<=set(files or {}),'Expected mutations must name explicit owned fixture files'
 directory=OUT/name
 if directory.exists():shutil.rmtree(directory)
 directory.mkdir(parents=True);data=image() if payload is None else payload
 (directory/'TEST.PRM').write_bytes(data);shutil.copyfile(BINARY,directory/'TERMINAL.EXE')
 if keyboard_file is not None:(directory/'TEST.KBD').write_bytes(keyboard_file)
 for filename,data_file in (files or {}).items():
  relative=Path(filename);assert relative.parts and not relative.is_absolute() and '..' not in relative.parts and '\\' not in filename and filename not in ('TEST.PRM','TERMINAL.EXE','PRMEDIT.EXE')
  (directory/relative).parent.mkdir(parents=True,exist_ok=True);(directory/relative).write_bytes(data_file)
 if child_binary is not None:shutil.copyfile(child_binary,directory/'PRMEDIT.EXE')
 elif child=='editor':shutil.copyfile(EDITOR,directory/'PRMEDIT.EXE')
 elif child=='probe':shutil.copyfile(OUT/'PROBE.EXE',directory/'PRMEDIT.EXE')
 elif child=='fail':
  (directory/'fail.asm').write_text('BITS 16\nSEGMENT _TEXT public class=CODE use16\n..start:\n mov ax,0x4c09\n int 0x21\nSEGMENT STACK stack class=STACK use16\n resb 256\n')
  subprocess.run(['nasm','-f','obj',str(directory/'fail.asm'),'-o',str(directory/'fail.obj')],check=True)
  subprocess.run(['wlink','system','dos','option','quiet','name',str(directory/'PRMEDIT.EXE'),'file',str(directory/'fail.obj')],check=True)
 subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/setup_watch.asm'),'-o',str(directory/'WATCH.COM')],check=True)
 (directory/'sampler.asm').write_text(SAMPLER)
 subprocess.run(['nasm','-f','bin',str(directory/'sampler.asm'),'-o',str(directory/'SNAP.COM')],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
 stop=threading.Event();peer_checks={};wire=bytearray();errors=[]
 def peer():
  conn=None
  try:
   post_sent=False;paused_at=None;pause_resumed=False
   while not stop.is_set():
    try:conn,_=server.accept();break
    except socket.timeout:pass
   if conn is None:return
   conn.settimeout(.05)
   # The DOS editor can run for several seconds. Probe until the terminal owns
   # the UART; do not infer readiness from the transport connection itself.
   end=time.monotonic()+15;next_send=0
   while time.monotonic()<end and not stop.is_set():
    if ready and time.monotonic()>=next_send:conn.sendall(b'\x1b[5n');next_send=time.monotonic()+.3
    try:block=conn.recv(4096)
    except socket.timeout:continue
    if not block:break
    wire.extend(block)
    if b'\x1b[0n' in wire:
     peer_checks['actual_terminal_ready_reply']=True
     conn.sendall(b'\x1b[2J\x1b[HSETUP READY\x1b[6n');break
   while not stop.is_set():
    if pause_after_input and paused_at is None and pause_after_input in wire:
     conn.sendall(b'\x13\x1b[5n');paused_at=time.monotonic()
    if paused_at is not None and not pause_resumed and time.monotonic()-paused_at>=1.25:
     conn.sendall(b'\x11');pause_resumed=True;peer_checks['controlled_pause_resumed']=True
    try:block=conn.recv(4096)
    except socket.timeout:continue
    if not block:break
    wire.extend(block)
    if b'\x1b[1;12R' in wire:peer_checks['actual_terminal_cursor_reply']=True
    if post_echo and not post_sent and b'ready' in wire:
     conn.sendall((post_banner if post_banner is not None else b' LIVE')+b'\x1b[6n'+(b'\x1b[0c' if expected_profile is not None else b''));post_sent=True
    if post_echo and (b'\x1b[1;6R' if profile_clear else b'\x1b[1;17R') in wire:peer_checks['post_editor_receive_render_and_cursor_reply']=True
    if expected_profile is not None and (b'\x1b[?1;2c' if expected_profile==6 else b'\x1b[?62;2c') in wire:peer_checks['post_editor_profile_device_reply']=True
  except OSError as error:
   if not stop.is_set():errors.append(str(error))
  finally:
   if conn is not None:conn.close()
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 schedule='ADDKEY p750 '+' p120 '.join(keys.split()) if keys else ('ADDKEY p750' if ready else '')
 if ready:schedule+=' p1800 a-x'
 branch=f'if errorlevel {expected+1} goto fail\nif errorlevel {expected} goto pass\ngoto fail' if expected else 'if errorlevel 1 goto fail\ngoto pass'
 environment_lines=['set PCPLUS=']
 for variable,value in (environment or {}).items():
  assert variable and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in variable)
  assert not any(c in value for c in '\r\n\0%<>|&')
  environment_lines.append('set '+variable+'='+value)
 environment_commands='\n'.join(environment_lines)
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype={cpu}
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount d "{directory}"
d:
{environment_commands}
WATCH T
SNAP B
{schedule}
TERMINAL {arguments}
{branch}
:pass
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
D:\\SNAP S
D:\\SNAP A
D:\\WATCH
exit
'''
 (directory/'dosbox.conf').write_text(config)
 try:
  with (directory/'dosbox.log').open('w') as log:proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(directory/'dosbox.conf')],cwd=directory,stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=25)
 finally:stop.set();thread.join(1);server.close()
 before=(directory/'BEFORE.BIN').read_bytes();after=(directory/'AFTER.BIN').read_bytes();screen=(directory/'SCREEN.BIN').read_bytes()
 checks={'expected_DOS_exit':proc.returncode==0 and (directory/'PASS.TXT').exists() and not (directory/'FAIL.TXT').exists(),'hardware_restored':len(before)==42 and before==after,'no_peer_errors':not errors,'no_recovery_files':not (directory/'PRMEDIT.BAK').exists() and not (directory/'PRMEDIT.$$$').exists()}
 if ready:
  checks.update(peer_checks);checks['both_peer_checks_seen']=len(peer_checks)==(3 if post_echo else 2)+(expected_profile is not None)+bool(pause_after_input)
  checks['actual_video_ready']=screen[:10:2]==b' LIVE' if profile_clear else screen[:22:2]==b'SETUP READY'
 else:checks['no_serial_output']=not wire
 if child=='probe' and ready:
  checks['child_entry_hardware_unchanged']=(directory/'CHILDHW.BIN').read_bytes()==before
  tail=(directory/'CHILDARG.BIN').read_bytes();expected_tail=b' TEST.PRM'
  checks['exact_direct_child_tail']=tail[:len(expected_tail)+2]==bytes([len(expected_tail)])+expected_tail+b'\r'
 samples=struct.unpack('<6H',(directory/'WATCH.BIN').read_bytes())
 checks['independent_timer_samples']=samples[0]==0x5355 and samples[1]>0
 if ready:checks['actual_configured_UART_divisor']=samples[2]==({1200:1,115200:2,19200:4}[rate] if rate_mask is None else rate_mask) and samples[4]>0
 else:checks['UART_never_observed_enabled']=samples[4]==0
 if line_mask is not None:checks['actual_configured_UART_line_format']=samples[5]==line_mask
 if keyboard_file is not None:checks['keyboard_fixture_unchanged']=(directory/'TEST.KBD').read_bytes()==keyboard_file
 for filename,data_file in (files or {}).items():
  target=directory/filename
  if filename in (expected_files or {}):
   expected_file=expected_files[filename]
   checks['fixture_expected_final_'+filename]=not target.exists() if expected_file is None else target.is_file() and target.read_bytes()==expected_file
  else:checks['fixture_unchanged_'+filename]=target.read_bytes()==data_file
 (directory/'serial.bin').write_bytes(wire)
 result={'case':name,'passed':all(checks.values()),'checks':checks,'expected_exit':expected,'arguments':arguments,'observed_errors':errors}
 (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],result
 print(name,'passed',flush=True);return result,(directory/'TEST.PRM').read_bytes()
def main():
 OUT.mkdir(parents=True,exist_ok=True);probe_child();cases=[]
 for name,kwargs,want in [
  ('cancel-continues-original',{'keys':'escape'},image()),
  ('save-then-import',{'keys':'tab home del del del del 1 1 5 2 0 0 f10 escape','rate':115200},image()[:2]+b'\x08\0'+image()[4:]),
  ('CLI-override-after-save',{'keys':'tab home del del del del 1 1 5 2 0 0 f10 escape','arguments':'/S @TEST.PRM 19200','rate':19200},image()[:2]+b'\x08\0'+image()[4:]),
  ('probe-before-UART',{'child':'probe'},image()),
  ('missing-child',{'child':'missing','expected':7,'ready':False},image()),
  ('failed-child',{'child':'fail','expected':7,'ready':False},image()),
  ('short-image',{'payload':image()[:-1],'expected':7,'ready':False},image()[:-1]),
  ('missing-explicit-config',{'arguments':'/S','expected':1,'ready':False},image()),
  ('non-leaf-config',{'arguments':'/S @D:\\TEST.PRM','expected':1,'ready':False},image()),
  ('invalid-directory-selectors',{'arguments':'/S @TEST.PRM /E:A.DIR /D:host','expected':7,'ready':False},image()),
  ('help-skips-setup',{'arguments':'/S /?','child':'probe','ready':False},image())]:
  result,raw=run(name,**kwargs);assert raw==want,name;result['checks']['exact_expected_PRM']=True;cases.append(result)
  if name in ('invalid-directory-selectors','help-skips-setup'):assert not (OUT/name/'CHILDHW.BIN').exists()
 # Repair a bad loaded field before the normal startup decoder sees it.
 raw=bytearray(image());raw[0x198]=2
 result,actual=run('repair-before-import',keys='f10 home del 0 f10 escape',payload=bytes(raw));assert actual==image();cases.append(result)
 sources=[ROOT/'src/terminal'/p for p in ['setup_startup.asm','options.asm','main.asm']]+[ROOT/'standalone/check_setup_model.py',ROOT/'standalone/test_terminal.py',ROOT/'standalone/setup_watch.asm',Path(__file__).resolve()]
 report={'passed':True,'cases':cases,'terminal_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'editor_sha256':hashlib.sha256(EDITOR.read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Actual DOS direct editor child before UART acquisition, then source-built terminal with loopback serial and independent hardware/video sampling. Synthetic PRMs and source-built child probes only. Not live reconfiguration during a connection, original PCSETUP parent-memory ABI, or physical modem validation.'}
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
