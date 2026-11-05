#!/usr/bin/env python3
"""Actual internal viewer during RX pressure with capture/HOLD and virtual PRN."""
import argparse,json,os,shutil,socket,struct,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
from build_path_session import ROOT,sha
from test_viewer_dialog_dos import page
from test_ansi_reference_dos import reference
FIRST=b'FIRST'+b'B'*600+b'\r\n';PAUSED=b'PAUSED\r\n';BURST=b'A'*3200+b'\r\n';LAST=b'LAST\r\n'
CASES={'capture':(1,0,0),'hold':(1,1,0),'capture-printer':(1,0,1),'hold-printer':(1,1,1),'printer':(0,0,1)}

def run(binary,out,name):
 capture,hold,printer=CASES[name];drive=out/name;drive.mkdir();package=drive/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE')
 raw=bytearray(fixture(initialize=0));struct.pack_into('<HH',raw,0x198,1,1)
 for at,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x196,0)]:struct.pack_into('<H',raw,at,value)
 (drive/'TEST.PRM').write_bytes(raw);(drive/'SNAP.ASM').write_text(SAMPLER)
 payload=b''.join(('L%03d\r\n'%i).encode() for i in range(1,73));(drive/'VIEW.DAT').write_bytes(payload)
 for source,target,flags in [('standalone/viewer_sinks_trace_install.asm','TRACE.COM',[]),('standalone/gateway_sinks_trace_dump.asm','TDUMP.COM',[]),('standalone/viewer_pressure_watch.asm','WATCH.COM',['-DWATCH_KIND=8']),(str(drive/'SNAP.ASM'),'SNAP.COM',[])]:
  subprocess.run(['nasm','-fbin',*flags,str(ROOT/source),'-o',str(drive/target)],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
 stop=threading.Event();wire=bytearray();sent=bytearray();checks={};errors=[]
 def peer():
  try:
   connection=None
   while not stop.is_set():
    try:connection,_=server.accept();break
    except socket.timeout:pass
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
     at=len(wire);sent.extend(data);connection.sendall(data+b'\x1b[5n');assert wait(b'\x1b[0n',4,at),'No fresh DSR after text'
    for _ in range(20):
     at=len(wire);connection.sendall(b'\x1b[5n')
     if wait(b'\x1b[0n',.15,at):break
    else:raise AssertionError('No initial DSR')
    assert wait(b'm1',7);text(FIRST)
    if hold:assert wait(b'mh',4);text(PAUSED)
    assert wait(b'ml',5)
    # Passive capture requires the real local page and the updated live frame
    # containing LAST, which is sent only after Escape and a normal remote key.
    assert not stop.wait(1.5);text(BURST);checks['fresh_DSR_after_viewer_burst']=True
    assert wait(b'm3',10);text(LAST);checks['post_viewer_keyboard_DSR']=True
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
 if hold:keys+=['a-f2','p300','m','h','p700']
 keys+=['m','l','p500','a-v','p500',*list('VIEW.DAT'),'enter','p5500','escape','p300']
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
WATCH T
SNAP B
ADDKEY {' '.join(keys)}
set PCPLUS=
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
WATCH
TDUMP
exit
''')
 try:
  with (drive/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=28)
 finally:stop.set();server.close();thread.join(timeout=1)
 read=lambda n:(drive/n).read_bytes() if (drive/n).exists() else b''
 observed=read('VPRESS.BIN');frame=observed[4018:8018];live=observed[8018:12018];trace=read('TRACE.BIN')
 head=struct.unpack_from('<10H',trace,6) if len(trace)==8218 else None
 records=[struct.unpack_from('<4H',trace,26+i*8) for i in range(min(head[2],1024))] if head else []
 opens=[(i,r) for i,r in enumerate(records) if r[0]==0x3da0]
 expected=FIRST+(b'' if hold else BURST)+LAST;printed=FIRST+(PAUSED if hold else b'')+BURST+LAST
 expected_live,cursor=reference(FIRST+(PAUSED if hold else b'')+BURST+LAST)
 words=struct.unpack_from('<9H',observed) if len(observed)==12083 else None
 checks.update(normal_exit=process.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),peer_ok=not errors,
  observed_viewer_and_restored_live=words is not None and words[:2]==(0x5656,15),
  exact_local_page=frame==page([('L%03d'%i).encode() for i in range(1,25)]),
  exact_updated_live_1920_cells=live[:3840]==expected_live,
  exact_updated_live_cursor=words is not None and words[7]==((cursor[0]-1)<<8)|(cursor[1]-1),
  exact_capture=read('CAP.LOG')==expected if capture else not (drive/'CAP.LOG').exists(),exact_PRN=read('PRINTER.RAW')==printed if printer else not read('PRINTER.RAW'),
  hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),startup_CWD=read('AFTERCD.TXT').strip()==b'D:\\',
  PRM_unchanged=read('TEST.PRM')==raw,binary_unchanged=sha(package/'TERMINAL.EXE')==sha(binary),
  viewer_file_unchanged=read('VIEW.DAT')==payload,
  trace_complete=head is not None and trace[:6]==b'GS21\x0f\0' and head[:2]==(0xc51b,1) and head[3]==0,one_private_readonly_open=len(opens)==1)
 observations={}
 if len(opens)==1:
  first,call=opens[0];ds=call[3];devices=[(i,r) for i,r in enumerate(records) if i>first and r[0]==0x4400 and r[3]==ds]
  checks['viewer_device_inspected']=bool(devices)
  if devices:
   device,info=devices[0];viewfd=info[1]
   reads=[i for i,r in enumerate(records) if device<i and r[0]>>8==0x3f and r[1]==viewfd]
   closes=[i for i,r in enumerate(records) if device<i and r[0]>>8==0x3e and r[1]==viewfd and r[3]==ds]
   checks['viewer_read_and_closed_once']=bool(reads) and len(closes)==1
   last=closes[0] if closes else len(records)
   checks['no_viewer_close_before_last_read']=bool(reads) and all(i<last for i in reads)
   if capture:
    before=[(i,r) for i,r in enumerate(records) if i<first and r[0]>>8==0x40 and r[2]==256 and r[3]==ds]
    checks['capture_wrote_before_viewer']=bool(before)
    if before:
     fd=before[-1][1][1];after=[i for i,r in enumerate(records) if i>last and r[0]>>8==0x40 and r[1]==fd and r[3]==ds]
     checks['same_capture_FD_after_viewer']=bool(after)
     if not hold:checks['capture_wrote_while_viewer_owned']=any(first<i<last and r[0]>>8==0x40 and r[1]==fd and r[3]==ds for i,r in enumerate(records))
     if after:checks['capture_not_closed_between_writes']=not any(before[-1][0]<i<after[-1] and r[0]>>8==0x3e and r[1]==fd and r[3]==ds for i,r in enumerate(records))
   observations=dict(parent_DS=ds,viewer_open_record=first,viewer_device_record=device,viewer_FD=viewfd,viewer_read_records=reads,viewer_close_record=last,record_count=head[2])
 (drive/'wire.bin').write_bytes(wire);(drive/'peer-text.bin').write_bytes(sent)
 result=dict(case=name,passed=all(checks.values()),checks=checks,observations=observations,errors=errors,capture_bytes=len(read('CAP.LOG')),printer_bytes=len(read('PRINTER.RAW')),binary_sha256=sha(binary),scope=__doc__+' Actual DOS8086/FPU-off COM1/BOTH,3202-byte RX while local view is open, raw DSR and later keyboard, exact virtualPRN/capture, passive local/updated live VGA and DOS trace. No stock server, physical printer/flow timing, modem carrier or analog acceptance.')
 (drive/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,{k:v for k,v in checks.items() if not v},errors,flush=True);assert result['passed'],result
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',choices=CASES,action='append');a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_file_viewer'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[run(binary,out,n) for n in a.case or CASES]
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 names=['standalone/test_viewer_sinks_dos.py','standalone/viewer_pressure_watch.asm','standalone/viewer_sinks_trace_install.asm','standalone/gateway_sinks_trace_dump.asm','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/test_viewer_dialog_dos.py','standalone/test_ansi_reference_dos.py']
 (out/'result.json').write_text(json.dumps(dict(passed=True,cases=cases,binary_sha256=sha(binary),sources={n:sha(ROOT/n) for n in names},original_inputs=[],scope=__doc__),indent=2)+'\n')
if __name__=='__main__':main()
