#!/usr/bin/env python3
"""Real DOS/PIT/keyboard/UART alert tests against an independent raw TCP peer."""
import argparse,itertools,json,os,re,shutil,socket,subprocess,threading,time
from pathlib import Path
from build_context_help import ROOT,sha
PAYLOAD=bytes(n for n in range(256) if n not in (17,19))*2

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',action='append',help='Subset, e.g.1-N-N-S; default50-case matrix')
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert all(x.is_relative_to(ROOT/'build') for x in (build,out));out.mkdir(exist_ok=False)
 m=json.loads((build/'manifest.json').read_text());assert m['passed'] and m['diagnostic_build'] and sha(build/'ALARM.EXE')==m['binary_sha256']
 inputs={**m['sources'],'standalone/test_alarm_dos_uart.py':sha(Path(__file__))};assert all(sha(ROOT/n)==h for n,h in inputs.items())
 cohort=[(port,flow,mode,'S') for port,flow,mode in itertools.product((1,2),'NSHB','NQKFB')]
 cohort += [(port,flow,'K','E') for port,flow in itertools.product((1,2),'NSHB')]
 cohort += [(1,'N','G','S'),(2,'S','G','E')]
 allowed={'-'.join(map(str,c)):c for c in cohort};selected=[allowed[n] for n in a.case] if a.case else cohort
 rows=[]
 for port,flow,mode,keyboard in selected:
  label=f'{port}-{flow}-{mode}-{keyboard}';folder=out/label;folder.mkdir();shutil.copyfile(build/'ALARM.EXE',folder/'ALARM.EXE')
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2);stop=threading.Event();done=threading.Event();wire=bytearray();events=[];errors=[];started=time.monotonic()
  def peer():
   try:
    connection=None
    while not stop.is_set():
     try:connection,_=server.accept();break
     except socket.timeout:continue
    if connection is None:return
    stage=0
    with connection:
     connection.settimeout(.1)
     while not stop.is_set():
      try:data=connection.recv(4096)
      except socket.timeout:continue
      if not data:events.append(dict(kind='EOF',seconds=time.monotonic()-started));break
      wire.extend(data);events.append(dict(kind='receive',hex=data.hex(),seconds=time.monotonic()-started))
      if b'R' in wire and not stage:
       packet=(b'\x13'+PAYLOAD+b'\x11') if flow in 'SB' else PAYLOAD
       connection.sendall(packet);events.append(dict(kind='send',hex=packet.hex(),seconds=time.monotonic()-started));stage=1
      if b'P' in wire and stage==1:
       connection.sendall(b'READY!');events.append(dict(kind='send',hex=b'READY!'.hex(),seconds=time.monotonic()-started));stage=2
   except OSError as error:
    if not stop.is_set():errors.append(str(error))
   finally:done.set()
  thread=threading.Thread(target=peer,daemon=True);thread.start()
  serial=[f'serial{i}=disabled' for i in range(1,5)];serial[port-1]=f'serial{port}=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1'
  (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\n'+'\n'.join(serial)+'\n[autoexec]\n@echo off\nmount c "'+str(folder)+'"\nc:\nALARM /S'+str(port)+':0003:03:'+flow+' '+mode+' '+keyboard+' >OUTPUT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
  code=None
  try:
   with (folder/'dosbox.log').open('w') as log:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=25).returncode
   done.wait(2)
  finally:stop.set();server.close();thread.join(1)
  (folder/'peer.json').write_text(json.dumps(dict(events=events,errors=errors),indent=2)+'\n');(folder/'wire.bin').write_bytes(wire)
  text=(folder/'OUTPUT.TXT').read_text() if (folder/'OUTPUT.TXT').exists() else ''
  match=re.fullmatch(r'ALARM UART COM(\d) ([NSHB]) ([NQKFBG]) ([SE]) (\d+) checks (\d+) callbacks (\d+) maximum (\d+) sound polls\s*',text)
  checks=dict(emulator_exit=code==0,DOS_exit=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),
   actual_assertions=bool(match) and (int(match[1]),match[2],match[3],match[4])==(port,flow,mode,keyboard) and int(match[5])>530 and int(match[6])>1 and 0<int(match[7])<=508,
   exact_received=(folder/'RX.BIN').exists() and (folder/'RX.BIN').read_bytes()==PAYLOAD,
   exact_wire=bytes(wire)==(b'\x11RPF\x13' if flow in 'SB' else b'RPF'),peer_clean=not errors and any(e['kind']=='EOF' for e in events),binary_unchanged=sha(folder/'ALARM.EXE')==m['binary_sha256'])
  row=dict(case=label,passed=all(checks.values()),checks=checks,assertions=int(match[5]) if match else None,callbacks=int(match[6]) if match else None,maximum=int(match[7]) if match else None,sound_polls=int(match[8]) if match else None,captures={str(f.relative_to(out)):sha(f) for f in folder.iterdir() if f.is_file()})
  rows.append(row);print(label,'PASS' if row['passed'] else 'FAIL',text.strip(),flush=True)
  result=dict(passed=len(rows)==len(selected) and all(r['passed'] for r in rows),full_matrix=not a.case,cases=rows,binary_sha256=m['binary_sha256'],inputs=inputs,payload_sha256=__import__('hashlib').sha256(PAYLOAD).hexdigest(),
   scope=__doc__+' Real banked PIT speaker, DOS clock, BIOS keys and UART ISR/foreground reads on8086. COM1/2 N/S/H/B; normal,quiet,key completion,service error,busy gates plus enhanced-key and foreign-generation recovery.508 exact bytes consumed during alert,followed byREADY exchange and UART/PIC/vector restoration. Muted emulator; no acoustic/physical BBS/timing or VM/parent policy acceptance. Nullmodem holds CTS ready and does not enforce RTS; software XOFF/XON explicit.')
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
  if not row['passed']:raise AssertionError(label)
 for n,h in inputs.items():assert sha(ROOT/n)==h,n
if __name__=='__main__':main()
