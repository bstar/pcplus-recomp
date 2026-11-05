#!/usr/bin/env python3
"""Actual parent IRQ/flow and private files across an 8086 DOS child."""
import argparse,hashlib,itertools,json,os,re,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
PAYLOAD=b'\0\x1a\x80\xff'*800
def run(binary,out,manifest,port,flow,tamper=False):
 drive=out/('COM'+str(port)+'-'+flow+('-tamper' if tamper else ''));drive.mkdir();package=drive/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 raw=bytearray(fixture());base=0x3f8 if port==1 else 0x2f8;irq=4 if port==1 else 3
 struct.pack_into('<HH',raw,0,port-1,6)
 struct.pack_into('<H',raw,0x174+2*(port-1),base);struct.pack_into('<H',raw,0x184+2*(port-1),irq)
 struct.pack_into('<HH',raw,0x198,int(flow in 'SB'),int(flow in 'HB'))
 for at,val in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x196,0)]:struct.pack_into('<H',raw,at,val)
 (drive/'TEST.PRM').write_bytes(raw)
 child=(ROOT/'standalone/gateway_files_child.asm').read_text()
 if tamper:
  marker=' mov ax,0x4c25\n int 0x21\n';assert child.count(marker)==1
  mutation=f''' mov dx,{base+1}
 xor al,al
 out dx,al
 mov ax,{0x2500+irq+8}
 mov dx,gateway_fake_irq
 int 0x21
 mov dx,{base+3}
 mov al,0x83
 out dx,al
 mov dx,{base}
 mov al,0x34
 out dx,al
 inc dx
 mov al,0x12
 out dx,al
 mov dx,{base+3}
 mov al,0x1e
 out dx,al
 mov dx,{base+4}
 mov al,3
 out dx,al
 mov dx,{base+2}
 mov al,1
 out dx,al
'''
  child=child.replace(marker,mutation+marker)+'''\ngateway_fake_irq:
 push ax
 mov al,0x20
 out 0x20,al
 pop ax
 iret
'''
 (drive/'SHELL.ASM').write_text(child)
 subprocess.run(['nasm','-fbin','-DGATEWAY_UART_CHILD','-DPORT_BASE='+str(base),'-DUART_IRQ='+str(irq),'-I'+str(ROOT/'standalone')+'/',str(drive/'SHELL.ASM'),'-o',str(drive/'SHELL.COM')],check=True)
 sampler=SAMPLER
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (drive/'SNAP.ASM').write_text(sampler);subprocess.run(['nasm','-fbin',str(drive/'SNAP.ASM'),'-o',str(drive/'SNAP.COM')],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
 stop=threading.Event();wire=bytearray();sent=[];errors=[]
 def peer():
  connection=None
  try:
   while not stop.is_set():
    try:connection,_=server.accept();break
    except socket.timeout:continue
   if connection is None:return
   with connection:
    connection.settimeout(.1)
    while not stop.is_set():
     try:chunk=connection.recv(4096)
     except socket.timeout:continue
     if not chunk:break
     wire.extend(chunk)
     if b'D' in wire and not sent:connection.sendall(PAYLOAD);sent.append(len(PAYLOAD))
  except OSError as e:
   if not stop.is_set():errors.append(str(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start();serial=[f'serial{i}=disabled' for i in range(1,5)]
 serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
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
{chr(10).join(serial)}
[autoexec]
@echo off
mount c "{package}"
mount d "{drive}"
d:
set PCPLUS=
D:\\SNAP B
ADDKEY p500 enter p500 enter
set COMSPEC=D:\\SHELL.COM
C:\\TERMINAL @D:\\TEST.PRM
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
D:\\SNAP A
exit
''')
 try:
  with (drive/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
 finally:stop.set();server.close();thread.join(timeout=1)
 report=(drive/'GFRESULT.BIN').read_bytes() if (drive/'GFRESULT.BIN').exists() else b''
 words=struct.unpack_from('<10H',report,116) if len(report)==136 else None
 ring=(drive/'GFRX.BIN').read_bytes() if (drive/'GFRX.BIN').exists() else b'';actual=b''
 if words and len(ring)==4096:actual=(ring+ring)[words[7]:words[7]+words[2]]
 shell=(drive/'GUSHELL.BIN').read_bytes() if (drive/'GUSHELL.BIN').exists() else b''
 checks=dict(normal_exit=process.returncode==0,application_success=(drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),report=len(report)==136,
  UART_begin_end=words is not None and words[:2]==(0,8 if tamper else 0),all_bytes_retained=actual==PAYLOAD,
  file_transaction_result=len(report)==136 and struct.unpack_from('<3H',report)==(0,0,37),
  private_descriptors_preserved=len(report)==136 and report[22:30]==report[30:38] and struct.unpack_from('<4H',report,38)==(65535,)*4,
  no_receive_loss=words is not None and words[3]==0,flow_queue_serviced=words is not None and words[4]==0,
  software_pause=words is not None and words[5]==int(flow in 'SB') and bytes(wire).count(b'\x13')==int(flow in 'SB'),
  low_water_resume=words is not None and words[9]==0x0b00 and bytes(wire).count(b'\x11')==int(flow in 'SB'),
  hardware_pause=words is not None and words[6]==int(flow in 'HB'),child_real_wait=len(shell)==16 and struct.unpack_from('<H',shell,14)[0]>=54,
  live_child_vector=len(shell)==16 and shell[:4]==shell[4:8],child_IRQ_enabled=len(shell)==16 and shell[8]==9 and shell[11]==9,
  child_framing=len(shell)==16 and shell[10]==3 and shell[13]==3,
  child_hardware_flow=len(shell)==16 and shell[12]==(9 if flow in 'HB' else 11),
  private_files_continue=all((drive/n).exists() and (drive/n).read_bytes()==b'AB' for n in ['CAPTURE.DAT','SNAP.DAT','MONITOR.DAT','HISTORY.DAT']),
  peer_payload_sent=sent==[len(PAYLOAD)] and not errors,
  startup_restored=(drive/'BEFORE.BIN').read_bytes()==(drive/'AFTER.BIN').read_bytes(),binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary))
 (drive/'wire.bin').write_bytes(wire);result=dict(passed=all(checks.values()),port=port,flow=flow,tamper=tamper,checks=checks,UART_words=words,wire_hex=wire.hex(),peer_errors=errors,child_asm_sha256=sha(drive/'SHELL.ASM'))
 (drive/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('COM'+str(port)+'/'+flow+('/tamper' if tamper else ''),{k:v for k,v in checks.items() if not v},flush=True);assert result['passed'],result
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--port',type=int,choices=[1,2],action='append');p.add_argument('--flow',choices=list('NSHB'),action='append');p.add_argument('--tamper',action='store_true');a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();m=json.loads(binary.with_name('manifest.json').read_text());assert m['diagnostic_gateway_uart_probe'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[run(binary,out,m,port,flow) for port,flow in itertools.product(a.port or [1,2],a.flow or 'NSHB')]
 if a.tamper:cases.append(run(binary,out,m,1,'S',tamper=True))
 sources=['standalone/test_gateway_uart_dos.py','standalone/gateway_files_child.asm','standalone/gateway_uart_child.inc','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__+' UART already acquired before probe, real DOS child with foreign DS, exact3200-byte receive ring and XOFF while the foreground is suspended. No physical modem, BBS, peer honoring RTS, display return or hotkey acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
