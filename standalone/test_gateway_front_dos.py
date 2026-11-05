#!/usr/bin/env python3
"""Actual Alt-F4/menu Gateway, independent BIOS frame observer and serial peer."""
import argparse,hashlib,json,os,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(binary,out,name):
 drive=out/name;drive.mkdir();package=drive/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE');(drive/'TARGET').mkdir()
 raw=bytearray(fixture(initialize=0));struct.pack_into('<HH',raw,0x198,1,1)
 for at,val in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x196,0)]:struct.pack_into('<H',raw,at,val)
 (drive/'TEST.PRM').write_bytes(raw)
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/gateway_front_watch.asm'),'-o',str(package/'GWWATCH.COM')],check=True)
 (drive/'SNAP.ASM').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(drive/'SNAP.ASM'),'-o',str(drive/'SNAP.COM')],check=True)
 child=(ROOT/'standalone/gateway_files_child.asm').read_text();marker=' mov ax,0x4c25\n int 0x21\n';assert child.count(marker)==1
 child=child.replace(marker,''' mov ax,0xd741
 mov bx,1
 int 0x2f
 mov ax,0x13
 int 0x10
'''+marker)
 (drive/'SHELL.ASM').write_text(child)
 subprocess.run(['nasm','-fbin','-DCHANGE_CWD','-DGATEWAY_UART_CHILD','-DPORT_BASE=0x3f8','-DUART_IRQ=4','-I'+str(ROOT/'standalone')+'/',str(drive/'SHELL.ASM'),'-o',str(drive/'SHELL.COM')],check=True)
 if name=='command':(drive/'GW.BAT').write_bytes(b'@echo off\r\nmd D:\\WITNESS\r\ncd D:\\TARGET\r\ncd >D:\\CHILDCD.TXT\r\nD:\\SHELL.COM\r\nexit\r\n')
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
 stop=threading.Event();wire=bytearray();checks={};errors=[];stages=[]
 def peer():
  connection=None
  try:
   while not stop.is_set():
    try:connection,_=server.accept();break
    except socket.timeout:continue
   if connection is None:return
   with connection:
    connection.settimeout(.05)
    def wait(token,seconds):
     deadline=time.monotonic()+seconds
     while time.monotonic()<deadline and not stop.is_set():
      if token in wire:return True
      try:data=connection.recv(4096)
      except socket.timeout:continue
      if not data:return False
      wire.extend(data)
     return token in wire
    ready=False
    for _ in range(20):
     connection.sendall(b'\x1b[5n')
     if wait(b'\x1b[0n',.15):ready=True;break
    checks['terminal_ready']=ready
    if not ready:return
    connection.sendall(b'\x1b[2J\x1b[H\x1b[0m\x1b[3;5HBEFORE\x1b[6n')
    checks['canonical_before_cursor']=wait(b'\x1b[3;11R',1)
    checks['real_child_started']=wait(b'D',5)
    if not checks['real_child_started']:return
    stages.append('child');connection.sendall(b'A'*3200)
    time.sleep(3.2)
    prior=len(wire);resumed=False
    for _ in range(20):
     connection.sendall(b'\x1b[5n')
     if wait(b'\x1b[0n',.15) and b'\x1b[0n' in wire[prior:]:resumed=True;break
     try:data=connection.recv(4096);wire.extend(data)
     except socket.timeout:pass
    checks['parser_resumes_without_return_key']=resumed
    while not stop.wait(.05):
     try:data=connection.recv(4096)
     except socket.timeout:continue
     if not data:break
     wire.extend(data)
  except OSError as e:
   if not stop.is_set():errors.append(str(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 key='a-z p150 a-f4' if name=='menu' else 'a-f4'
 if name=='command':key+=' p600 g w enter'
 comspec='Z:\\COMMAND.COM' if name=='command' else 'D:\\SHELL.COM'
 cfg=drive/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{package}"
mount d "{drive}"
d:
C:\\GWWATCH T
D:\\SNAP B
ADDKEY p500 enter p1500 {key} p6000 a-x
set PCPLUS=
set COMSPEC={comspec}
C:\\TERMINAL @D:\\TEST.PRM
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
cd>D:\\AFTERCD.TXT
D:\\SNAP A
C:\\GWWATCH D
exit
''')
 try:
  with (drive/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
 finally:stop.set();server.close();thread.join(timeout=1)
 report=(drive/'GWVIEW.BIN').read_bytes() if (drive/'GWVIEW.BIN').exists() else b'';words=struct.unpack_from('<12H',report) if len(report)==16024 else None
 before=report[24:8024];after=report[8024:]
 checks.update(normal_exit=process.returncode==0,application_success=(drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),observer_complete=words is not None and words[:4]==(0x474f,1,1,1),
  exact_frame=words is not None and before[:4000]==after[:4000],cursor_shape=words is not None and words[6]==words[7] and words[8]==words[9],mode_rows=words is not None and words[4:6]==(25,25) and words[10:12]==(0x5003,0x5003),
  software_flow=b'\x13' in wire and b'\x11' in wire,child_executed=(drive/'CHILD.BIN').exists(),startup_CWD=(drive/'AFTERCD.TXT').read_text().strip()=='D:\\',
  hardware_vectors=(drive/'BEFORE.BIN').read_bytes()==(drive/'AFTER.BIN').read_bytes(),peer_ok=not errors,binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary))
 if name=='command':checks.update(command_created_directory=(drive/'WITNESS').is_dir(),command_changed_directory=(drive/'CHILDCD.TXT').read_text().strip()=='D:\\TARGET')
 (drive/'wire.bin').write_bytes(wire);result=dict(case=name,passed=all(checks.values()),checks=checks,observer=words,peer_errors=errors,wire_hex=wire.hex())
 (drive/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,{k:v for k,v in checks.items() if not v},flush=True);assert result['passed'],result
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--case',choices=['direct','menu','command'],action='append');a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_gateway_frontend'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[run(binary,out,name) for name in a.case or ['direct','menu','command']]
 sources=['standalone/test_gateway_front_dos.py','standalone/gateway_front_watch.asm','standalone/gateway_files_child.asm','standalone/gateway_uart_child.inc','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__+' Normal application keyboard/menu route, graphics child, serial traffic and passive frame/cursor observation. No physical or external BBS acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
