#!/usr/bin/env python3
"""Bind actual DOS EMULATE/parent replies while retaining the failing capacity gate."""
import argparse,json,struct
from pathlib import Path
from build_context_help import ROOT,sha
from package_connection_test import render_capability

def minimum(path):
 b=path.read_bytes();h=struct.unpack_from('<14H',b);size=(h[2]-1)*512+(h[1]or 512)
 return ((size-h[4]*16+15)//16+h[5])*16+256

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name,passed=True):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed']==passed,name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 products={};manifests={}
 for name,folder in [('TERMINAL.EXE','emulate-rpc-parent-20261107'),('ASPECT.EXE','emulate-rpc-child-20261107')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256'] and not m.get('original_inputs',[])
  for n,h in m['sources'].items():
   assert Path(n).parts[0]not in ('analysis','build','.git') and sha(ROOT/n)==h,n;sources[n]=h
  products[name]=dict(sha256=m['binary_sha256'],minimum_including_PSP=minimum(root/name));manifests[name]=m
 assert manifests['TERMINAL.EXE']['experimental_aspect_emulate_policy'] and manifests['ASPECT.EXE']['experimental_emulate_VM']
 assert render_capability(ROOT/'build/emulate-rpc-parent-20261107/TERMINAL.EXE')==20
 normal=load('build/emulate-rpc-dos-profile-final-20261107/result.json');failed=load('build/emulate-rpc-dos-capacity-20261107/result.json',False)
 for r in (normal,failed):
  assert r['binary_sha256']==products['TERMINAL.EXE']['sha256'] and r['interpreter_sha256']==products['ASPECT.EXE']['sha256']
  assert r['emulate_profile_switch'] and r['clock_queries'] and r['cpu']=='386'
 assert len(normal['checks'])==26 and all(normal['checks'].values()) and normal['checks']['both_profile_DA_pairs'] and normal['checks']['profile_reset_replaces_old_view']
 wire=ROOT/'build/connection-dos/emulate-rpc-dos-profile-final-20261107/serial.bin'
 data=wire.read_bytes();assert data.count(b'PROFILE4\r\x1b[?62;2cPROFILE6\r\x1b[?1;2c')==2 and data.count(b'FIRSTOK\r')==2
 for n in ('serial.bin','SCREEN.BIN','FIRST.ASX','TEST.PRM'):
  path=wire.parent/n;receipts[str(path.relative_to(ROOT))]=sha(path)
 asx=(wire.parent/'FIRST.ASX').read_bytes();assert asx.count(bytes([0x2f,4]))==asx.count(bytes([0x2f,6]))==1
 failures=[k for k,v in failed['checks'].items()if not v];assert len(failed['checks'])==30 and len(failures)==8 and failed['held_streams']
 native=load('build/emulate-rpc-native-owner-checks-20261107/result.json');assert native['native_bytes']==15 and native['cases']==768
 controls={}
 for name,folder,expected in [('TERMINAL.EXE','emulate-rpc-parent-control-20261107','689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06'),('ASPECT.EXE','emulate-rpc-child-control-20261107','b4f0aecc7a6538920711c2fa866324d2ddad856883a437cbb2f125cd0e26efbe')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256']==expected
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  controls[name]=dict(sha256=expected,minimum_including_PSP=minimum(root/name))
 assert products['TERMINAL.EXE']['minimum_including_PSP']==479760 and products['ASPECT.EXE']['minimum_including_PSP']==131344
 sources['standalone/record_aspect_emulate_rpc.py']=sha(Path(__file__))
 sources['standalone/package_connection_test.py']=sha(ROOT/'standalone/package_connection_test.py')
 report=dict(passed=False,profile_execution_passed=True,capacity_accepted=False,release_accepted=False,installed_changed=False,
  products=products,controls=controls,sources=sources,receipts=receipts,
  summary=dict(capability=20,actual_DOS_checks=26,actual_profile_pairs=2,native_bytes=15,native_CPU_cases=768,capacity_checks=30,capacity_failures=failures),
  limitations=['Unaccepted memory composition: simple actual profile workflow passes; six held streams/three nested children fails8of30 checks. Do not deploy this candidate or infer full session acceptance.',
   'Real DOS/parent/native VM used with a synthetic serial peer. Peer sends actual DA queries; no terminal replies are manufactured. Old banner preservation is inapplicable after full reset; initial CPR order and exact final ACK6 view replace that final-screen check.',
   'Version20 is required by both halves; negative version/MCB/lease and child modal/fault paths require expanded acceptance. Parent source retains existing checks, but normal success does not prove their negative behavior.',
   'No new cold-source proof, current Enigma/Synchronet/package, receive-stall, fatal-reset/WHEN fault or physical acceptance. Ordinary689/b4f0 controls remain exact; installed R59A85A8 unchanged. Full parity remains open.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('Recorded UNACCEPTED EMULATE RPC:26 actual DOS checks pass,8of30 capacity checks fail')
if __name__=='__main__':main()
