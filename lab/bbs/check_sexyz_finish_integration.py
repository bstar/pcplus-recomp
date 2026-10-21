#!/usr/bin/env python3
"""Real candidate helper closing-tail faults after an unchanged full-size upload."""
import argparse,ctypes as C,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import Fixture,P,U,h
from audio_upload import payload


class TailProbe(Fixture):
 def __init__(self,*args,tail,**kw):
  self.tail=tail;self.closing=False;self.delivered=bytearray()
  super().__init__(*args,**kw)
 def write(self,ctx,data,n):
  body=C.string_at(data,n);actual=self.tail if body==b'OO' else body
  if body==b'OO':self.closing=True
  self.tx.extend(body)
  if actual:self.peer.stdin.write(actual);self.peer.stdin.flush()
  self.delivered.extend(actual);return 0


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();candidate=a.candidate.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 executable=out/'bin/sexyz';executable.parent.mkdir();shutil.copyfile(candidate,executable);executable.chmod(0o755)
 assert sha(executable)==sha(candidate)
 ini=executable.with_suffix('.ini');ini.write_text('[ZMODEM]\nRecvTimeout=1\n')
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 library=out/'session.so';subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
  '-shared','-fPIC',*[str(p) for p in sources],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U]
 bad=bytearray(h(8));bad[-3]=ord('0') if bad[-3]!=ord('0') else ord('1')
 cases=[('queued-closing-headers',h(8)+h(7)+b'OO',0),('flow-between-Os',b'O\x11\x93O',0),
  ('bad-CRC',bytes(bad)+b'OO',1),('nonzero-position',h(8,1)+b'OO',1),
  ('noise-containing-OO',b'NOISEOO',1),('single-O',b'O',1),('missing-OO',b'',1),
  ('five-CANs',b'\x18'*5,1),('ten-closing-headers',h(8)*10+b'OO',1),
  ('endless-flow-byte-ceiling',b'\x11'*600,1)]
 expected=payload();rows=[]
 for name,tail,wanted in cases:
  folder=out/name;folder.mkdir();command=[str(executable),'-telnet','-8','rz',str(folder)+'/']
  with (folder/'stderr.log').open('xb') as log:
   peer=subprocess.Popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   try:
    f=TailProbe(lib,peer=peer,sources=[('FINISH.BIN',expected)],tail=tail)
    status=f.run(True);started=time.monotonic();peer.wait(timeout=4);elapsed=time.monotonic()-started
    assert status==0 and f.closing and not f.source and f.session.files==1
    assert sum(e[0]=='close' for e in f.events)==1
    assert peer.returncode==wanted and (folder/'FINISH.BIN').read_bytes()==expected,(name,peer.returncode)
    text=(folder/'stderr.log').read_text(errors='replace');assert 'Reading '+str(ini) in text
    if wanted:assert 'LoC RXFIN: closing OO unconfirmed' in text
    if name in ('single-O','missing-OO'):assert .8<=elapsed<3,(name,elapsed)
    (folder/'sender-attempted.bin').write_bytes(f.tx);(folder/'sender-delivered.bin').write_bytes(f.delivered)
    rows.append({'case':name,'passed':True,'expected_receiver_exit':wanted,'receiver_exit':peer.returncode,
     'actual_retirement_wait_seconds':elapsed,'host_sender_status':status,'source_closed_once':sum(e[0]=='close' for e in f.events)==1,
     'installed_exact_bytes':len(expected),'installed_sha256':sha(folder/'FINISH.BIN'),
     'wire_and_log_sha256':{n:sha(folder/n) for n in ['sender-attempted.bin','sender-delivered.bin','stderr.log']}})
   finally:
    if peer.poll() is None:peer.terminate();peer.wait(timeout=5)
 result={'passed':True,'cases':rows,'candidate_sha256':sha(candidate),'isolated_copy_sha256':sha(executable),
  'ini_sha256':sha(ini),'checker_sha256':sha(Path(__file__)),
  'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sources},
  'scope':'Actual Nix candidate receiver subprocesses and unchanged maintained host C sender, full11521-byte all-octet upload per case. Only the final closing transport is fault-injected. Candidate accepts queued valid closing headers/flow and rejects corrupt, missing, canceled or over-limit tails within its configured bound. Sender fixture success alone does not confirm delivery or receiver success; both are recorded. Isolated adjacent INI and binary copy, no server/runtime/DOS-product change. Not DOS/audio/BBS/physical acceptance.'}
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(rows),'real candidate receiver closing cases')


if __name__=='__main__':main()
