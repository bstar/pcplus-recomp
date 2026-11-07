#!/usr/bin/env python3
"""Record linked ALARM staging and the failed DOS load gate, not acceptance."""
import json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def footprint(path):
 w=struct.unpack_from('<14H',path.read_bytes());assert w[0]==0x5a4d
 module=w[2]*512-(512-w[1] if w[1] else 0)-w[4]*16
 return (((module+15)//16)+w[5]+16)*16

def main():
 parent=ROOT/'build/terminal-alarm-policy-first-20261106';child=ROOT/'build/aspect-alarm-vm-first-20261106'
 sources={};receipts={}
 for folder,binary in ((parent,'TERMINAL.EXE'),(child,'ASPECT.EXE')):
  manifest=folder/'manifest.json';r=json.loads(manifest.read_text());assert sha(folder/binary)==r['binary_sha256']
  receipts[str(manifest.relative_to(ROOT))]=sha(manifest)
  for name,digest in r['sources'].items():
   assert sha(ROOT/name)==digest,name
   if name in sources:assert sources[name]==digest,name
   sources[name]=digest
 native=ROOT/'build/alarm-vm-native-regression-20261106/result.json';r=json.loads(native.read_text());assert r['passed'] and r['cases']==348 and r['native_bytes']==120
 receipts[str(native.relative_to(ROOT))]=sha(native)
 case=ROOT/'build/aspect-alarm-vm-dos/exec-observed-20261106/alarm-vm-plain-terminal';r=json.loads((case/'result.json').read_text())
 assert not r['passed'] and r['passive_observer_header'][:4]==[0x524e,1,1,0] and r['passive_observer_header'][6]==8
 assert b'KEYREADY' not in (case/'serial.bin').read_bytes()
 default=sha(ROOT/'build/aspect-runner/ASPECT.EXE');assert default=='91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
 for name in ('standalone/test_aspect_alarm_vm_dos.py','standalone/record_alarm_vm_staging.py','standalone/test_aspect_pause_when_dos.py','standalone/test_aspect_keys_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_aspect_script_window_dos.py','standalone/test_aspect_window_query_dos.py','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py'):sources[name]=sha(ROOT/name)
 report=dict(builds_verified=True,runtime_accepted=False,released=False,sources=sources,receipts=receipts,
  artifacts={str(p.relative_to(ROOT)):sha(p) for p in case.iterdir() if p.is_file()},
  parent_sha256=sha(parent/'TERMINAL.EXE'),child_sha256=sha(child/'ASPECT.EXE'),default_interpreter_sha256=default,
  minimum_process_bytes_including_PSP=dict(parent=footprint(parent/'TERMINAL.EXE'),child=footprint(child/'ASPECT.EXE'),preceding_clock_child=footprint(ROOT/'build/aspect-clock-compact-final-20261106/ASPECT.EXE')),
  evidence=dict(native_cases=348,native_exact_bytes=120,DOS_EXEC_carry_error=8,child_exit_observed=False,ALARM_entered=False),
  limitations=['Linked opt-in opcode/wrapper/serviced alert and current-parent capability19 policy, without successful VM execution yet.',
   'Passive-observer test reached actual dialing and attempted ASPECT, but DOS EXEC returned8 (insufficient memory) before any child exit/KEYREADY. Does not establish a TSR-free production failure or the sole cause of memory pressure.',
   'Earlier legacy fixture failed display/directory admission with both accepted and new parents; configured display fields resolved that preliminary fixture issue. Original observer kind restriction was replaced by active-PROGRAM admission and read-only EXEC carry/error capture.',
   'No ALARM policy/runtime, WHEN/action/parser, six-stream/nested-child, BBS or physical acceptance for this linked variant. No package selection/deployment or private configuration changes.'],
  next='Measure/fund resident memory while preserving stacks, six streams, buffers and original native operand capacity; repeat actual VM/default/explicit/key/sound/WHEN/render and parent/BBS gates.',scope=__doc__)
 out=ROOT/'docs/validation/aspect-alarm-vm-staging.json';out.write_text(json.dumps(report,indent=2)+'\n');print('Staging recorded: builds verified; runtime NOT accepted; DOS EXEC8')
if __name__=='__main__':main()
