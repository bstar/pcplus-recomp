#!/usr/bin/env python3
"""Actual foreground Gateway with capture/HOLD/PRN and a hostile child JFT probe."""
import argparse,hashlib,json,os,re,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FIRST=b'FIRST\r\n';PAUSED=b'PAUSED\r\n';BURST=b'A'*3200+b'\r\n';LAST=b'LAST\r\n'
CASES={'capture':(True,False,False),'hold':(True,True,False),'capture-printer':(True,False,True),'hold-printer':(True,True,True),'printer':(False,False,True)}

def run(binary,out,name):
 capture,hold,printer=CASES[name];drive=out/name;drive.mkdir();package=drive/'package';package.mkdir();(drive/'TARGET').mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 raw=bytearray(fixture(initialize=0));struct.pack_into('<HH',raw,0x198,1,1)
 for at,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x196,0)]:struct.pack_into('<H',raw,at,value)
 (drive/'TEST.PRM').write_bytes(raw);(drive/'SNAP.ASM').write_text(SAMPLER)
 for source,target,flags in [('standalone/gateway_files_child.asm',drive/'SHELL.COM',['-DGATEWAY_UART_CHILD','-DCHANGE_CWD','-DPORT_BASE=0x3f8','-DUART_IRQ=4','-I'+str(ROOT/'standalone')+'/']),('standalone/gateway_sinks_trace_install.asm',drive/'TRACE.COM',[]),('standalone/gateway_sinks_trace_dump.asm',drive/'TDUMP.COM',[]),(str(drive/'SNAP.ASM'),drive/'SNAP.COM',[])]:
  subprocess.run(['nasm','-fbin',*flags,str(ROOT/source),'-o',str(target)],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
 stop=threading.Event();wire=bytearray();sent=bytearray();checks={};errors=[]
 def peer():
  connection=None
  try:
   while not stop.is_set():
    try:connection,_=server.accept();break
    except socket.timeout:continue
   if connection is None:return
   with connection:
    connection.settimeout(.05)
    def wait(token,seconds,start=0):
     deadline=time.monotonic()+seconds
     while time.monotonic()<deadline and not stop.is_set():
      if token in wire[start:]:return True
      try:data=connection.recv(4096)
      except socket.timeout:continue
      if not data:return False
      wire.extend(data)
     return token in wire[start:]
    def text(data):
     at=len(wire);sent.extend(data);connection.sendall(data+b'\x1b[5n')
     assert wait(b'\x1b[0n',3,at),'No fresh DSR after text'
    ready=False
    for _ in range(20):
     at=len(wire);connection.sendall(b'\x1b[5n')
     if wait(b'\x1b[0n',.15,at):ready=True;break
    checks['initial_DSR']=ready;assert ready
    assert wait(b'm1',7);text(FIRST);checks['first_text_consumed']=True
    if hold:assert wait(b'm2',4);text(PAUSED);checks['held_text_consumed']=True
    assert wait(b'D',5);checks['actual_child_uart_marker']=True
    sent.extend(BURST);connection.sendall(BURST)
    assert wait(b'm3',9);checks['post_child_keyboard_without_return_prompt']=True;text(LAST)
    assert wait(b'ready',5);text(b'');checks['post_close_keyboard_DSR']=True
    while not stop.wait(.05):
     try:data=connection.recv(4096)
     except socket.timeout:continue
     if not data:break
     wire.extend(data)
  except Exception as e:
   if not stop.is_set():errors.append(repr(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 keys=['p500','enter','p800']
 if capture:keys+=['a-f1','p300',*list('D:\\CAP.LOG'),'enter','p300']
 if printer:keys+=['a-l','p300']
 keys+=['m','1','p1000']
 if hold:keys+=['a-f2','p300','m','2','p700']
 keys+=['a-f4','p4300']
 if hold:keys+=['a-f2','p300']
 keys+=['m','3','p1200']
 if capture:keys+=['a-f1','p400']
 if printer:keys+=['a-l','p400']
 keys+=list('ready')+['p400','a-x']
 cfg=drive/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 12000
[mixer]
nosound=true
[parallel]
parallel1={'file append:'+str(drive/'PRINTER.RAW') if printer else 'disabled'}
parallel2=disabled
parallel3=disabled
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
TRACE
SNAP B
ADDKEY {' '.join(keys)}
set PCPLUS=
set COMSPEC=D:\\SHELL.COM
C:\\TERMINAL @D:\\TEST.PRM
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
cd>D:\\AFTERCD.TXT
SNAP S
SNAP A
TDUMP
exit
''')
 try:
  with (drive/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25)
 finally:stop.set();server.close();thread.join(timeout=1)
 read=lambda leaf:(drive/leaf).read_bytes() if (drive/leaf).exists() else b''
 uart=read('GUSHELL.BIN')
 child=read('CHILD.BIN');child_words=struct.unpack('<32H',child) if len(child)==64 else None
 trace=read('TRACE.BIN');records=[];header=struct.unpack_from('<10H',trace,6) if len(trace)==8218 else None
 if header:
  records=[struct.unpack_from('<4H',trace,26+i*8) for i in range(min(header[2],1024))]
 entries={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 parameter_offset=entries['process_parameters'][1]
 # COMMAND.COM also EXECs the sampler and collector. Select the application's
 # immutable mapped parameter-block offset from the actual DOS entry registers.
 execs=[(i,r) for i,r in enumerate(records) if r[0]==0x4b00 and r[1]==parameter_offset]
 expected_capture=FIRST+(b'' if hold else BURST)+LAST
 expected_printer=FIRST+(PAUSED if hold else b'')+BURST+LAST
 checks.update(normal_exit=process.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),peer_ok=not errors,
  child_private_writes_and_closes_refused=child_words is not None and child_words[:30]==(6,6)*15,
  child_own_file_and_empty_tail=child_words is not None and child_words[30:]==(5,0xd00) and read('OWN.DAT')==b'Y',
  exact_capture=read('CAP.LOG')==expected_capture if capture else not (drive/'CAP.LOG').exists(),
  exact_PRN=read('PRINTER.RAW')==expected_printer if printer else not read('PRINTER.RAW'),
  software_flow_pair=b'\x13' in wire and b'\x11' in wire,
  child_live_IRQ_and_RTS_pressure=len(uart)==16 and uart[:4]==uart[4:8] and uart[8]==uart[11]==9 and uart[9]==0x0b and uart[12]==9 and struct.unpack_from('<H',uart,14)[0]>=54,
  hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
  startup_CWD=read('AFTERCD.TXT').strip()==b'D:\\',binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary),
  passive_trace_retired=bool(header) and trace[:4]==b'GS21' and struct.unpack_from('<H',trace,4)[0]==15 and header[:2]==(0xc51b,1) and header[3]==0,
  one_actual_EXEC=len(execs)==1)
 observations={}
 if len(execs)==1:
  pos,entry=execs[0];parent_ds=entry[3]
  writes=[(i,r) for i,r in enumerate(records) if r[0]>>8==0x40 and r[3]==parent_ds and r[2]>1]
  closes=[(i,r) for i,r in enumerate(records) if r[0]>>8==0x3e and r[3]==parent_ds]
  observations=dict(parent_DS=parent_ds,EXEC_record=pos,parent_writes=writes,parent_closes=closes,record_count=header[2])
  if printer:
   fd=6 if capture else 5
   checks['printer_not_closed_before_Gateway']=sum(i<pos and r[1]==fd for i,r in closes)==(0 if capture else 1)
  if capture:
   prior=[(i,r) for i,r in writes if i<pos];later=[(i,r) for i,r in writes if i>pos]
   checks['same_capture_handle_before_after_EXEC']=bool(prior and later) and prior[-1][1][1]==later[0][1][1]
   if prior and later:
    fd=prior[-1][1][1];checks['capture_not_closed_at_Gateway']=not any(prior[-1][0]<i<later[-1][0] and r[1]==fd for i,r in closes)
    if printer:checks['printer_not_closed_before_post_return_capture']=not any(i<later[-1][0] and r[1]==6 for i,r in closes)
 (drive/'wire.bin').write_bytes(wire);(drive/'peer-text.bin').write_bytes(sent)
 result=dict(case=name,passed=all(checks.values()),checks=checks,observations=observations,peer_errors=errors,binary_sha256=sha(binary),keys=' '.join(keys),capture_bytes=len(read('CAP.LOG')),printer_bytes=len(read('PRINTER.RAW')),expected_capture_sha256=hashlib.sha256(expected_capture).hexdigest() if capture else None,expected_printer_sha256=hashlib.sha256(expected_printer).hexdigest() if printer else None,scope=__doc__+' Real8086/FPU-off DOSBox UART, DOS filesystem and file-only virtual PRN. Controlled3200-byte in-flight pressure; no stock BBS, physical printer, hardware flow timing or analog acceptance.')
 (drive/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,{k:v for k,v in checks.items() if not v},errors,flush=True);assert result['passed'],result
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--case',choices=CASES,action='append');a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_gateway_frontend'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[run(binary,out,name) for name in a.case or CASES]
 sources=['standalone/test_gateway_sinks_dos.py','standalone/gateway_sinks_trace_install.asm','standalone/gateway_sinks_trace_dump.asm','standalone/gateway_files_child.asm','standalone/gateway_uart_child.inc','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__),indent=2)+'\n')
if __name__=='__main__':main()
