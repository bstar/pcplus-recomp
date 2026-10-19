#!/usr/bin/env python3
"""Actual DOS terminal/BIOS/UART/files against pinned independent lrzsz.
Synthetic owned media, explicit runtime freeze, no product callbacks replaced.
"""
import argparse,fcntl,hashlib,json,os,select,shutil,socket,subprocess,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer
from test_terminal_ymodem_dos import BatchPeer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-zmodem-dos';BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def r_automatic(recipe):return bool(recipe.get('automatic'))
class ZPeer(Peer):
 def __init__(self,r,path):
  self.path=path;self.child=None;self.peer_exit=None;self.resume_timeout=r.get('resume_timeout',80)
  super().__init__(r)
 def run(self):
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();deadline=time.monotonic()+20
    if not r_automatic(self.recipe):
     while b'\x18' not in self.pending and time.monotonic()<deadline:self.receive()
     assert b'\x18' in self.pending,'No actual DOS ZMODEM start'
    self.log('protocol-start')
    sending=self.recipe['direction']=='tx'
    self.command=[shutil.which('rz' if sending else 'sz'),'-b','-q']+self.recipe['flags']
    if not sending:self.command+=(['-8','-L','8192'] if self.recipe.get('zedzap') else ['-L','1024'])+[n for n,_ in self.recipe['files']]
    with (self.path/'peer-stderr.log').open('wb') as log:
     self.child=subprocess.Popen(self.command,cwd=self.path/'PEER',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
     self.child.stdin.write(self.pending);self.pending.clear();deadline=time.monotonic()+max(65,self.recipe.get('transfer_timeout',65))
     while time.monotonic()<deadline and not self.stop.is_set():
      ready,_,_=select.select([conn,self.child.stdout],[],[],.1)
      if self.child.stdout in ready:
       data=os.read(self.child.stdout.fileno(),4096)
       if data:self.send(data)
       elif self.child.poll() is not None:break
      if conn in ready:
       data=conn.recv(4096)
       if not data:raise EOFError('DOS disconnected during ZMODEM')
       self.wire.extend(data);self.child.stdin.write(data)
     self.peer_exit=self.child.wait(timeout=5)
     assert self.peer_exit==0,('Independent peer failed',self.peer_exit)
    self.log('peer-completed',exit_code=self.peer_exit)
    self.checks['independent_peer_exit_zero']=True
    BatchPeer.resume(self);self.log('terminal-resumed')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(repr(error))
  finally:
   if self.child:
    if self.child.poll() is None:self.child.kill();self.child.wait()
    self.child.stdin.close();self.child.stdout.close()
   self.server.close()

def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False)
 for n in ('RECV','SEND','PEER'):(out/n).mkdir()
 source=out/('SEND' if r['direction']=='tx' else 'PEER')
 for name,data in r['files']:(source/name).write_bytes(data)
 before_sources={p.name:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in source.iterdir()}
 (out/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 peer=ZPeer(r,out);peer.thread.start()
 filename='D:\\RECV\\' if r['direction']=='rx' else 'D:\\SEND\\*.BIN'
 keys=['p1500','a-r' if r['direction']=='rx' else 'a-s','p300','f2','p100','f2','p200']+list(filename)+['enter','p'+str(a.after_ms),'r','e','a','d','y','p1500','a-x']
 arguments=''
 if r_automatic(r):
  from terminal_config_fixtures import image
  config_image=image(port=1,autodownload=1,download=b'D:\\RECV\\')
  (out/'AUTO.PRM').write_bytes(config_image);arguments=' @AUTO.PRM'
  keys=['p'+str(a.after_ms),'r','e','a','d','y','p1500','a-x']
 serial='\n'.join(f'serial{i}='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==1 else 'disabled') for i in range(1,5))
 conf=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{serial}
[autoexec]
@echo off
mount c "{BINARY.parent}"
mount d "{out}"
d:
SNAP B
ADDKEY {' '.join(keys)}
C:\\TERMINAL COM1 38400 8N1 HARD{arguments}
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto capture
:fail
echo FAIL>FAIL.TXT
:capture
SNAP S
SNAP A
exit
'''
 (out/'dosbox.conf').write_text(conf);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=a.timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.thread.join(6);assert not peer.thread.is_alive(),'Owned peer did not stop'
 def read(name):return (out/name).read_bytes() if (out/name).exists() else b''
 destination=out/('RECV' if r['direction']=='rx' else 'PEER')
 checks=dict(peer.checks)
 checks.update(no_peer_errors=not peer.errors,DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
  hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
  exact_destination={p.name:p.read_bytes() for p in destination.iterdir()}==dict(r['files']),
  source_unchanged=before_sources=={p.name:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in source.iterdir()},
  posttransfer_DSR=bool(checks.get('posttransfer_DSR')),posttransfer_keyboard=bool(checks.get('posttransfer_keyboard')),
  screen_restored=len(read('SCREEN.BIN'))==4000 and read('SCREEN.BIN')[:28:2]==b'AFTER TRANSFER',
  no_stages=not any(p.name.upper().startswith(('PCRX.','PCZRX.')) for p in out.rglob('*')),
  binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256)
 if r_automatic(r):
  checks['saved_preferences_unchanged']=read('AUTO.PRM')==config_image
  checks['no_manual_transfer_keys']='a-r' not in keys and 'f2' not in keys and 'enter' not in keys
 (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent)
 result=dict(passed=all(checks.values()),case=r['name'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,peer_command=getattr(peer,'command',None),peer_exit=peer.peer_exit,
  keys=keys,recipe_bounds=dict(after_ms=a.after_ms,transfer_timeout=r['transfer_timeout'],resume_timeout=r['resume_timeout'],DOS_timeout=a.timeout),files={n:hashlib.sha256(d).hexdigest() for n,d in r['files']},scope=('Actual DOSBox-X saved automatic invitation without transfer keys; ' if r_automatic(r) else 'Actual DOSBox-X BIOS F2 protocol selection; ')+ ' maintained terminal CONFIG_CODE/far callbacks, UART ISR, checked batch source seek/read and staged receive files with independent pinned lrzsz stdio peer. Synthetic local media, no BBS login or physical modem claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],json.dumps(result),flush=True);return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--jobs',type=int,default=2,choices=(1,2));p.add_argument('--after-ms',type=int,default=15000);p.add_argument('--large',action='store_true');p.add_argument('--case',action='append');p.add_argument('--timeout',type=int,default=100);p.add_argument('--zedzap',action='store_true');p.add_argument('--automatic',action='store_true');a=p.parse_args()
 assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256
 OUT.mkdir(exist_ok=True);files=[('EMPTY.BIN',b''),('ODD.BIN',b'A'),('ALL.BIN',bytes(range(256))*(257 if a.large else 4)+b'\0\x1a\xff@\r')]
 rows=[dict(name='rx-default',direction='rx',flags=[],files=files),dict(name='rx-crc16',direction='rx',flags=['-o'],files=files),dict(name='tx-default',direction='tx',flags=[],files=files),dict(name='tx-escape',direction='tx',flags=['-e'],files=files)]
 rows=[r for r in rows if (not a.case or r['name'] in a.case) and (not a.automatic or r['direction']=='rx')];assert rows
 for r in rows:r['automatic']=a.automatic
 for r in rows:r['transfer_timeout']=max(65,a.after_ms/1000+10);r['zedzap']=a.zedzap;r['resume_timeout']=min(a.timeout,max(10,a.after_ms/1000+10))
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with ThreadPoolExecutor(max_workers=a.jobs) as pool:results=list(pool.map(lambda r:run_case(r,a),rows))
 report=dict(passed=all(r['passed'] for r in results),binary_sha256=a.sha256,cases=results)
 (OUT/a.label/'checks.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
