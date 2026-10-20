#!/usr/bin/env python3
"""Compile/test an isolated control-helper candidate with Nix GCC, not the VM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import shutil
import socket
import struct
import subprocess
import threading
import time
import tty
import urllib.request

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
REVISION='b1752e4d0039e0cff72735924e03aa99922723a8'
PINS={'modemd-ctrl.c':'95d30103668f3e4e894136a81841a2be64ebcddcaef8e2afb58bdb2b326a3385',
      'wire.h':'6d978be175e76f64c3bd7ddf21db39379759f2097f699050cb229d206c832b0d'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frame(kind,data=b''):return struct.pack('<HB',len(data)+1,kind)+data


def actual_pty(executable,out):
 out.mkdir();control=socket.socket(socket.AF_UNIX);control.bind(str(out/'control.sock'));control.listen(1);control.settimeout(3)
 master,slave=pty.openpty();tty.setraw(slave);os.set_blocking(master,False)
 env=dict(os.environ,SYNTHMODEM_CONTROL_PATH=str(out/'control.sock'),SYNTHMODEM_PTY_PATH=os.ttyname(slave))
 packet_buf=bytearray();packets=[];data_rx=bytearray()
 def receive_until(conn,predicate,timeout=2):
  deadline=time.monotonic()+timeout
  while not predicate():
   remaining=deadline-time.monotonic()
   assert remaining>0,'Control packet deadline'
   assert select.select([conn],[],[],remaining)[0]
   data=conn.recv(65536);assert data,'Control EOF'
   packet_buf.extend(data)
   while len(packet_buf)>=3:
    size,kind=struct.unpack_from('<HB',packet_buf);assert size>=1
    if len(packet_buf)<size+2:break
    body=bytes(packet_buf[3:size+2]);packets.append((kind,body))
    if kind==0x15:data_rx.extend(body)
    del packet_buf[:size+2]
 def read_exact(count,timeout=8):
  data=bytearray();deadline=time.monotonic()+timeout
  while len(data)<count:
   remaining=deadline-time.monotonic();assert remaining>0,('PTY deadline',len(data),count)
   assert select.select([master],[],[],remaining)[0]
   try:part=os.read(master,min(97,count-len(data)))
   except BlockingIOError:continue
   assert part;data.extend(part);time.sleep(.0002)
  return bytes(data)
 log=(out/'helper.log').open('w');child=subprocess.Popen([str(executable)],env=env,stdout=log,stderr=log)
 checks={};writer=None;reverse_writer=None;reverse_stop=threading.Event();errors=[]
 try:
  conn,_=control.accept()
  with conn:
   conn.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
   receive_until(conn,lambda:bool(packets))
   # Two coalesced frames, actual kernel read/parse/PTY, no state injection.
   conn.sendall(frame(0x11,b'ONE')+frame(0x11,b'TWO'))
   checks['coalesced_AT_payload_and_CR_order']=read_exact(8)==b'ONE\rTWO\r'
   os.write(master,b'\r\nCONNECT 14400\r\n')
   receive_until(conn,lambda:any(b'"connect"' in data for _,data in packets))
   payload=bytes((i*37+(i>>8))&255 for i in range(262147))
   def send():
    try:
     for at in range(0,len(payload),4093):conn.sendall(frame(0x14,payload[at:at+4093]))
    except Exception as error:errors.append(repr(error))
   writer=threading.Thread(target=send,daemon=True);writer.start()
   # Hold the real PTY master unread. The bounded helper must backpressure its
   # host socket rather than absorb/discard the remaining source.
   time.sleep(.15);checks['host_sender_backpressured']=writer.is_alive()
   received=read_exact(len(payload));writer.join(3)
   checks['full_binary_payload_exact']=received==payload
   checks['writer_completed']=not writer.is_alive() and not errors
   (out/'received.bin').write_bytes(received)
   # Reverse pressure: stop reading the host channel while the PTY source
   # produces far more data than its kernel buffers can absorb.
   reverse=bytes(range(256))*4096+b'XYZ';reverse_errors=[]
   def send_reverse():
    at=0;deadline=time.monotonic()+10
    try:
     while at<len(reverse) and not reverse_stop.is_set():
      assert time.monotonic()<deadline
      try:at+=os.write(master,reverse[at:at+4096])
      except BlockingIOError:select.select([],[master],[],.05)
    except Exception as error:reverse_errors.append(repr(error))
   reverse_writer=threading.Thread(target=send_reverse,daemon=True);reverse_writer.start()
   time.sleep(.15);checks['paused_host_backpressures_PTY_writer']=reverse_writer.is_alive()
   # A blocked host-output path must still accept/forward opposite-direction
   # data, rather than getting stuck inside a blocking write loop.
   probe=b'REVERSE STALL LIVE';conn.sendall(frame(0x14,probe))
   checks['opposite_direction_live_during_host_stall']=read_exact(len(probe),timeout=.6)==probe
   receive_until(conn,lambda:len(data_rx)>=len(reverse),timeout=8)
   reverse_writer.join(2)
   checks['reverse_payload_exact']=bytes(data_rx)==reverse
   checks['reverse_writer_completed']=not reverse_writer.is_alive() and not reverse_errors
   (out/'reverse-received.bin').write_bytes(data_rx)
   # Guard timing must not block inbound data service for 2.2 seconds.
   packets.clear();started=time.monotonic();conn.sendall(frame(0x16));time.sleep(.05)
   os.write(master,b'PEER LIVE')
   receive_until(conn,lambda:any(b'PEER LIVE' in data for _,data in packets),timeout=.6)
   checks['PTY_read_serviced_during_hangup_guard']=time.monotonic()-started<.7
   escaped=read_exact(3);first=time.monotonic();command=read_exact(4);last=time.monotonic()
   checks['hangup_bytes_and_guards']=escaped==b'+++' and command==b'ATH\r' and first-started>=1.05 and last-first>=1.05
   # SIGTERM remains responsive when another write is stuck behind a full PTY.
   writer=threading.Thread(target=send,daemon=True);writer.start();time.sleep(.1)
   reverse_writer=threading.Thread(target=send_reverse,daemon=True);reverse_writer.start();time.sleep(.15)
   checks['both_directions_stalled_before_signal']=writer.is_alive() and reverse_writer.is_alive()
   reverse_stop.set()
   start=time.monotonic();child.terminate();child.wait(timeout=1)
   checks['signal_responsive_with_both_outputs_pending']=time.monotonic()-start<1 and child.returncode==0
  writer.join(2)
 finally:
  reverse_stop.set()
  if child.poll() is None:child.kill();child.wait()
  control.close();os.close(master);os.close(slave);log.close()
  if writer:writer.join(2)
  if reverse_writer:reverse_writer.join(2)
 result={'passed':all(checks.values()),'checks':checks,'payload_size':len(payload),
         'payload_sha256':hashlib.sha256(payload).hexdigest(),
         'reverse_payload_size':len(reverse),'reverse_payload_sha256':hashlib.sha256(reverse).hexdigest(),
         'scope':'Actual host-built helper process, Linux raw PTY and Unix control socket. No VM, slmodemd, DSP, SIP/audio or DOS.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 assert result['passed'],result
 return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 inputs={x.name:sha(x) for x in HERE.iterdir() if x.is_file()}
 for variant in ['stock','candidate']:
  target=out/variant/'vm/ctrl';target.mkdir(parents=True)
  for name,h in PINS.items():
   b=urllib.request.urlopen(f'https://raw.githubusercontent.com/synexo/synthmodem/{REVISION}/vm/ctrl/{name}',timeout=20).read()
   assert hashlib.sha256(b).hexdigest()==h; (target/name).write_bytes(b)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'control.patch')],cwd=out/'candidate',check=True)
 reports={};commands=[]
 for variant in ['stock','candidate']:
  target=out/variant/'vm/ctrl';exe=out/(variant+'-faults')
  cmd=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(target),str(HERE/'faults.c'),'-o',str(exe)]
  if variant=='candidate':cmd.insert(1,'-DFIXED')
  subprocess.run(cmd,check=True);commands.append(cmd)
  run=subprocess.run([str(exe)],capture_output=True,text=True)
  (out/(variant+'-faults.log')).write_text(run.stdout+run.stderr)
  assert run.returncode==0,run.stderr
  reports[variant]=json.loads(run.stdout)
 executable=out/'control-helper'
 cmd=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',str(out/'candidate/vm/ctrl/modemd-ctrl.c'),'-o',str(executable)]
 subprocess.run(cmd,check=True);commands.append(cmd)
 reports['actual_PTY']=actual_pty(executable,out/'pty')
 assert inputs=={x.name:sha(x) for x in HERE.iterdir() if x.is_file()},'Inputs changed during run'
 result={'passed':True,'upstream_revision':REVISION,'upstream_sha256':PINS,'lab_input_sha256':inputs,
         'candidate_sha256':sha(out/'candidate/vm/ctrl/modemd-ctrl.c'),'host_executable_sha256':sha(executable),
         'gcc':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
         'reports':reports,'commands':commands,
         'limits':['Host build only; VM images/prebuilts unchanged.','Node/DSP pressure propagation, VM integration and physical modem acceptance remain open.']}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
