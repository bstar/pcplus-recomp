#!/usr/bin/env python3
"""Record exact snapshot checks and rejected application capacity, plus overlay ABI controls."""
import json
from pathlib import Path
from build_path_session import ROOT,sha


def main():
 receipts={}
 def read(name):
  p=ROOT/name;receipts[name]=sha(p);return json.loads(p.read_text())
 component=read('build/disk-snapshot-component-bound-20261108/result.json')
 integrated=read('build/disk-snapshot-integrated-final-20261108/result.json')
 legacy=read('build/disk-snapshot-legacy-20261108/result.json')
 for report,count in [(component,642),(integrated,8108),(legacy,8819)]:
  assert report['passed'] and report['checks']==count
  for name,h in report['sources'].items():assert sha(ROOT/name)==h,name
 assert component['quarantine_checks']==16 and len(component['quarantined_files'])==2
 assert integrated['disk_snapshots'] and not legacy['disk_snapshots']
 child=read('build/disk-snapshot-child-final-20261108/manifest.json')
 control=read('build/disk-snapshot-disabled-control-20261108/manifest.json')
 for folder,m in [('disk-snapshot-child-final-20261108',child),('disk-snapshot-disabled-control-20261108',control)]:
  assert sha(ROOT/'build'/folder/'ASPECT.EXE')==m['binary_sha256'] and not m['original_inputs']
  for name,h in m['sources'].items():assert sha(ROOT/name)==h,name
 assert child['experimental_disk_script_snapshots'] and child['experimental_deferred_help_resource']
 assert control['binary_sha256']=='9b1b5f98d6e2a4d64e4154a5d2f97240c1455787e5a7ab5d8d4c1cf37c473fe0'
 capacity=read('build/disk-snapshot-capacity-final-20261108/result.json')
 assert not capacity['passed'] and capacity['interpreter_sha256']==child['binary_sha256']
 assert capacity['held_streams'] and capacity['cpu']=='8086' and not capacity['checks']['held_files_preserved']
 screen=ROOT/'build/connection-dos/disk-snapshot-capacity-final-20261108/screen.txt'
 assert 'invalid operand (error 7, opcode 41, step 17, native 4)' in screen.read_text()
 receipts[str(screen.relative_to(ROOT))]=sha(screen)
 overlay=[]
 for name,manager in [('overlay-plain-v2-20261108','none'),('overlay-standard-v2-20261108','standard')]:
  report=read('build/'+name+'/result.json')
  assert report['passed'] and report['callbacks']==300 and report['code_model']=='small' and report['manager']==manager
  assert report['checker_sha256']==sha(ROOT/'standalone/check_standard_overlay_dos.py')
  for leaf,h in report['sources'].items():assert sha(ROOT/'build'/name/leaf)==h
  assert sha(ROOT/'build'/name/'OVERLAY.EXE')==report['binary_sha256']
  overlay.append(dict(manager=manager,callbacks=300,binary_sha256=report['binary_sha256']))
 result=dict(schema=1,checkpoint_verified=True,package_eligible=False,
  component_checks=642,quarantine_checks=16,integrated_checks=8108,legacy_checks=8819,
  child_sha256=child['binary_sha256'],disabled_sha256=control['binary_sha256'],
  child_layout=child['GET_bank_layout'],capacity_passed=False,
  overlay_ABI_controls=overlay,receipts=receipts,recorder_sha256=sha(Path(__file__)),
  installed_changed=False,selector_changed=False,physical_verified=False,
  limits=['Disk snapshots preserve all512 bytes and ownership metadata; no hashes or smaller buffers.',
   'Full child regresses to fifth-file allocation refusal because extra resident code outweighs the available idle memory.',
   'No snapshot IO occurs before the failed PROGRAM workload; component success is not full application admission.',
   'Overlay controls prove small-root far-cdecl A/B/A and resident callbacks only; no application overlay lifetime/unwind/IRQ claim.',
   'Initial overlay probes incorrectly declared the second function near; fixed plain/standard controls pass. Small-manager variant is not qualified.',
   'Prepared package, installation and Host-last work order unchanged.'])
 (ROOT/'docs/validation/disk-snapshot-experiment.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Verified snapshots and overlay ABI; recorded failed capacity; no promotion')


if __name__=='__main__':main()
