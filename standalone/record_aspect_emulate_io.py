#!/usr/bin/env python3
"""Bind actual strict-KBD failure recovery and receive-overlap evidence."""
import argparse,json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={};products={};cases=[]
 def bind(items):
  for n,h in items.items():assert sha(ROOT/n)==h,n;sources[n]=h
 for name,folder in [('TERMINAL.EXE','emulate-rpc-parent-20261107'),('ASPECT.EXE','emulate-rpc-child-checked-20261107')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256'];products[name]=m['binary_sha256'];bind(m['sources'])
 for case,cpu in [('missing','386'),('short','8086'),('receive','386')]:
  folder='emulate-io-'+case+'-release-20261107';root=ROOT/'build'/folder;path=root/'result.json';r=json.loads(path.read_text());assert r['passed'] and r['products']==products and r['case']==case and r['cpu']==cpu
  assert len(r['checks'])==34 and all(r['checks'].values());bind(r['sources']);receipts[str(path.relative_to(ROOT))]=sha(path)
  drive=ROOT/'build/connection-dos'/folder
  raw=(drive/'RXSTAT.BIN').read_bytes();assert len(raw)==16 and struct.unpack('<2H',raw[:4])==(0xe620,1)
  assert r['receive_observer']['maximum_dropped']==r['receive_observer']['maximum_serial_status']==0
  exits=r['observer']['exits'];assert len(exits)==4 and [e['error']for e in exits]==([0]*4 if case=='receive'else[5,0,0,0])
  if case=='receive':
   assert r['rounds']==128 and r['receive_observer']['read_entries']==130 and r['receive_observer']['pending_entries']>0
   assert r['receive_observer']['maximum_queued']>0 and 0<r['receive_timing']['waiting']<r['receive_timing']['done']
   wire=(drive/'serial.bin').read_bytes();part=wire.split(b'RXREADY\r',1)[1].split(b'RXDONE\r',1)[0];assert part.replace(b'RXWAIT\r',b'',1)==b'a'*512
  else:assert exits[0]['opcode']==47 and r['checks']['old_profile_survives_failed_EMULATE']
  for n in ('EMUWATCH.ASM','EMUWATCH.COM','SCENE.ASP','SIX.ASP','MISSING.ASP','FIRST.ASP'):
   receipts[str((root/n).relative_to(ROOT))]=sha(root/n)
  for n in ('serial.bin','peer-state.json','EXITSTAT.BIN','RXSTAT.BIN','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','TEST.KBD','SCENE.ASX','SIX.ASX','MISSING.ASX','FIRST.ASX'):
   receipts[str((drive/n).relative_to(ROOT))]=sha(drive/n)
  cases.append(dict(case=case,cpu=cpu,checks=34,exit_errors=[e['error']for e in exits],receive=r['receive_observer'],peer_observed_seconds=r['receive_timing']))
 sources['standalone/record_aspect_emulate_io.py']=sha(Path(__file__))
 report=dict(passed=True,release_accepted=False,installed_changed=False,products=products,sources=sources,receipts=receipts,cases=cases,original_inputs=[],
  fixture_history=['Initial generic harness attempted immutability verification of BACK.KBD after intentional rename; mutable backup is now staged separately and its final state asserted.',
   'Minimal KBD initially omitted the normal Enter binding (slot78); normal and keypad Enter now explicitly bind CR. Native errors/recovery already passed; the missing CR was fixture policy.',
   'First receive peer sent RXEND at a fixed time while128 switches still ran; native idle could consume it before WAITFOR. All512 markers acknowledged, but later keys raced the waiting script. Peer now waits for the real RXWAIT marker. No product changes.'],
  limitations=['Ordinary products and actual DOS native VM/RPC/strict reader/UART execute with synthetic modem/files and a passive resident observer. The hook reads state only, without DOS calls, UART reads or application writes; memory/timing footprint differs from unobserved capacity tests.',
   'Receive case sends1536 ASCII bytes in32 paced chunks, recognizes512 native WHEN TRANSMIT patterns and performs128 explicit KBD-backed switches. Samples establish queued receive overlap at parent DOS entry points; they do not measure worst-case interrupt latency, full-ring pressure, sustained line-rate headroom, hardware CTS or physical/SIP/audio performance.',
   'Host ready/waiting/done intervals include VM/file/reset/receive/pattern/TX and scheduling costs. They are not individual import/reset duration bounds or a16MHz386SX benchmark.',
   'Failure DA replies establish prior ANSI identity after native error5. Later exact reset view, successful scripts, native owner fields and restored keyboard are checked; arbitrary close ambiguity, asynchronous fatal-reset and every prior screen cell are separate gates.',
   'Named build folder suffix release is a test label only; no release selected/deployed. Native fatal-reset/abort expansion, matched capability20 package/source reproduction and physical acceptance remain open.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE strict IO',[(c['case'],c['cpu'],c['checks'])for c in cases])
if __name__=='__main__':main()
