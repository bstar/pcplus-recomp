#!/usr/bin/env python3
"""Retain a real stock-helper closing counterexample against a reference rz.

The maintained host C sender runs unchanged. Its fixture delays only delivery
of the required closing OO, after the actual receiver's ZFIN. This is a peer
subprocess test, not an actual DOS, audio, BBS or physical acceptance.
"""
import argparse,ctypes as C,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import Fixture,P,U
from enigma_transfer import HELPER
from audio_upload import payload


class ClosingProbe(Fixture):
 def __init__(self,*args,**kw):
  self.OO_attempted=False;self.exited_before_OO=None;self.hold_ns=None
  self.closed_peer=False;self.delivered=bytearray()
  super().__init__(*args,**kw)
 def write(self,ctx,data,n):
  body=C.string_at(data,n)
  if body==b'OO':
   self.OO_attempted=True;start=time.monotonic_ns()
   try:self.peer.wait(timeout=.35)
   except subprocess.TimeoutExpired:self.exited_before_OO=False
   else:self.exited_before_OO=True;self.closed_peer=True
   self.hold_ns=time.monotonic_ns()-start
  if self.closed_peer:
   # Keep attempted and delivered wire separate. A closed pipe is an actual
   # transport failure here; never pretend the withheld OO reached the peer.
   self.tx.extend(body);return 65534
  result=super().write(ctx,data,n)
  if not result:self.delivered.extend(body)
  return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--candidate',type=Path);p.add_argument('--source-baseline',type=Path)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 out.mkdir(parents=True)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 library=out/'session.so'
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
  '-shared','-fPIC',*[str(p) for p in sources],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U]
 rows=[];expected=payload();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 receivers=[('stock-SEXYZ',HELPER)]
 if a.source_baseline:receivers.append(('source-SEXYZ',a.source_baseline.resolve()))
 if a.candidate:receivers.append(('candidate-SEXYZ',a.candidate.resolve()))
 receivers.append(('reference-lrzsz',Path(shutil.which('rz'))))
 for kind,executable in receivers:
  folder=out/kind;folder.mkdir()
  command=[str(executable),'-telnet','-8','rz',str(folder)+'/'] if kind!='reference-lrzsz' else [str(executable),'-b','-q']
  with (folder/'stderr.log').open('xb') as log:
   peer=subprocess.Popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   try:
    fixture=ClosingProbe(lib,peer=peer,sources=[('FINISH.BIN',expected)])
    status=fixture.run(True);peer.wait(timeout=5)
    rest=peer.stdout.read();target=folder/'FINISH.BIN'
    assert fixture.OO_attempted and not fixture.source and fixture.session.files==1
    assert target.read_bytes()==expected and peer.returncode==0
    assert sum(e[0]=='close' for e in fixture.events)==1
    early=kind in ('stock-SEXYZ','source-SEXYZ')
    assert fixture.exited_before_OO==early
    assert status==(3 if early else 0),(kind,status)
    assert (fixture.delivered[-2:]!=b'OO') if early else fixture.delivered[-2:]==b'OO'
    for name,body in [('sender-attempted.bin',fixture.tx),('sender-delivered.bin',fixture.delivered),
                      ('receiver-consumed.bin',fixture.peer_wire),('receiver-unconsumed.bin',rest)]:
     with (folder/name).open('xb') as f:f.write(body)
    rows.append({'receiver':kind,'counterexample_reproduced':early,
     'receiver_exited_while_OO_withheld':fixture.exited_before_OO,
     'withheld_observation_ns':fixture.hold_ns,'host_sender_status':status,
     'receiver_exit':peer.returncode,'file_bytes':len(expected),'file_sha256':sha(target),
     'source_closed_once':True,'command':command,'receiver_sha256':sha(Path(command[0])),
     'attempted_wire_bytes':len(fixture.tx),'delivered_wire_bytes':len(fixture.delivered),
     'wire_sha256':{n:sha(folder/n) for n in ['sender-attempted.bin','sender-delivered.bin','receiver-consumed.bin','receiver-unconsumed.bin','stderr.log']}})
   finally:
    if peer.poll() is None:peer.terminate();peer.wait(timeout=5)
 result={'evidence_consistent':True,'stock_counterexample_reproduced':True,'cases':rows,
  'candidate_waits_for_OO':None if not a.candidate else not next(r for r in rows if r['receiver']=='candidate-SEXYZ')['receiver_exited_while_OO_withheld'],
  'library_sha256':sha(library),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},
  'checker_sha256':sha(Path(__file__)),
  'scope':'Real shipped stock SEXYZ3.6, optional same-source baseline/candidate, and independent pinned lrzsz receiver subprocesses; unchanged maintained host C sender. Same11521-byte all-octet file, actual receiver ZFIN then350ms withheld OO. Exact files and single source close in every case. Stock exits before OO; candidate when selected and reference stay live and consume OO. Closed-pipe host status is not a DOS status or an audio result. No server/runtime/DOS-product modification, fabricated receiver replies or acceptance-gate waiver.'}
 with (out/'checks.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'counterexample_reproduced':True,'cases':[{k:r[k] for k in ['receiver','receiver_exited_while_OO_withheld','host_sender_status','receiver_exit','file_bytes']} for r in rows]},indent=2))


if __name__=='__main__':main()
