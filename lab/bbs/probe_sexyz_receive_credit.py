#!/usr/bin/env python3
"""Measure stock sender packet/checkpoint sizes for explicit receiver offers."""
import argparse,ctypes as C,json,shutil,subprocess,sys,time
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from enigma_transfer import HELPER
from prepare_audio_pressure_download import payload,NAME
from audit_zmodem import audit_batch,audit_controls,scan
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import Fixture,P,U,h


class CreditProbe(Fixture):
 def __init__(self,*args,offer,**kwargs):
  self.offer=offer;self.replacements=0;self.trace=[];super().__init__(*args,**kwargs)
 def read(self,context,seconds):
  value=super().read(context,seconds)
  if value<256:self.trace.append(dict(direction='bbs',offset=len(self.peer_wire)-1,size=1,seconds=time.monotonic()))
  return value
 def write(self,context,data,n):
  wire=C.string_at(data,n)
  if wire==h(1,0x23002000):wire=h(1,self.offer);self.replacements+=1
  offset=len(self.tx);result=super().write(context,C.cast(C.c_char_p(wire),P),len(wire))
  assert not result;self.trace.append(dict(direction='dos',offset=offset,size=len(wire),seconds=time.monotonic()))
  return result


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--helper',type=Path,default=HELPER,help='Explicit stock or isolated source-built helper; never changes the BBS')
 a=p.parse_args();out=a.output.resolve();helper=a.helper.resolve();assert helper.is_file()
 helper_hash=sha(helper);compiler=Path(shutil.which('gcc')).resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')];library=out/'session.so'
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in sources],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U];expected=payload();rows=[]
 variants=[('baseline8KiB-overlap',8192,3),('1KiB-overlap',1024,3),('256-byte-overlap',256,3),('1KiB-no-overlap',1024,1)]
 for name,credit,flags in variants:
  folder=out/name;folder.mkdir();source=folder/NAME;source.write_bytes(expected);offer=(32|flags)<<24|credit
  with (folder/'helper.stderr').open('xb') as log:
   peer=subprocess.Popen([str(helper),'-raw','-8','sz',NAME],cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   try:
    f=CreditProbe(lib,peer=peer,offer=offer);status=f.run();peer.wait(timeout=10)
    assert status==peer.returncode==0 and not f.errors and f.received=={NAME:expected}
    wire=bytes(f.peer_wire);opposite=bytes(f.tx);protocol=audit_batch(wire,{NAME:expected})
    for file in protocol['files']:assert file.pop('source')==expected
    (folder/'sender.bin').write_bytes(wire);(folder/'receiver.bin').write_bytes(opposite)
    (folder/'trace.json').write_text(json.dumps(f.trace,separators=(',',':'))+'\n')
    try:protocol['controls']=audit_controls(protocol,opposite,f.trace,'bbs',time.monotonic()+1)
    except AssertionError as exc:
     failure=dict(passed=False,error=str(exc),native_status=status,peer_exit=peer.returncode,exact_received_source=f.received=={NAME:expected},
      receiver_offers=f.replacements,protocol=protocol,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_zmodem.py']})
     (folder/'control-timing-failure.json').write_text(json.dumps(failure,indent=2)+'\n');raise
    parts=protocol['files'][0]['packets'];groups=[];pending=0
    for packet in parts:
     pending+=packet['length']
     if packet['ending'] in (104,107):groups.append(pending);pending=0
    assert not pending
    (folder/'sender.bin').write_bytes(wire);(folder/'receiver.bin').write_bytes(opposite)
    (folder/'trace.json').write_text(json.dumps(f.trace,separators=(',',':'))+'\n')
    (folder/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    checks=dict(exact_native_fixture_file=f.received[NAME]==expected,complete_independent_CRC_source_finish_controls=True,
     exact65797_accounting=f.session.files==1 and f.session.bytes==len(expected),real_stock_helper_exit_zero=peer.returncode==0,
     explicit_ZRINIT_only_override=f.replacements>=2 and all(x['position']==offer for x in scan(opposite) if x['type']==1),source_unchanged=source.read_bytes()==expected)
    assert all(checks.values())
    row=dict(name=name,passed=True,checks=checks,advertised_credit=credit,CANOVIO=bool(flags&2),ZRINIT_position=offer,
     max_packet_payload=max(p['length'] for p in parts),max_synchronous_group_payload=max(groups),packet_lengths=[p['length'] for p in parts],synchronous_groups=groups,
     protocol_received_bytes=len(wire),protocol_reply_bytes=len(opposite),verified_replays=sum(p['replayed'] for p in parts),
     captures_sha256={q.name:sha(q) for q in folder.iterdir() if q.is_file()})
    rows.append(row);print(json.dumps({k:row[k] for k in ('name','advertised_credit','CANOVIO','max_packet_payload','max_synchronous_group_payload')}),flush=True)
   finally:
    if peer.poll() is None:peer.kill();peer.wait()
    peer.stdin.close();peer.stdout.close()
 assert sha(helper)==helper_hash
 result=dict(passed=True,cases=rows,helper_path=str(helper),helper_sha256=helper_hash,stock_BBS_helper=helper==HELPER.resolve(),source_bytes=len(expected),
  compiler_path=str(compiler),compiler_sha256=sha(compiler),compiler_version=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
  inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__).resolve(),*sources,*[ROOT/'src/transfer'/n for n in ('zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h')],ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'lab/bbs/prepare_audio_pressure_download.py',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock',ROOT/'tools/dev']},
  library_sha256=sha(library),
  scope=('Capability experiment with unchanged stock BBS helper. ' if helper==HELPER.resolve() else 'Capability experiment with explicitly selected isolated helper candidate. ')+
   'Helper uses -raw -8 sz, maintained host C receiver and in-memory storage callbacks. Wrapper changes only complete ZRINIT offers, retaining all source/CRC/finish/control checks. No DOS/BBS/audio/timing/pressure/physical acceptance; packet/group sizes describe fast local pipes. A small advertised credit or cleared CANOVIO is not assumed to cap the sender packet; measured behavior guides the next slow-path candidate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(rows)}))


if __name__=='__main__':main()
