#!/usr/bin/env python3
"""Bind actual storage evidence and the baseline application's memory limits."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);a=p.parse_args()
 receipt=a.receipt.resolve();proof=a.proof.resolve()
 assert all(p.is_relative_to(ROOT/'build')for p in (receipt,proof))
 r=json.loads(receipt.read_text());q=json.loads(proof.read_text())
 assert r['passed'] and q['passed'] and r['checks']==q['checks']=={'REAL':28,'FAULT':37}
 assert r['binaries']==q['binaries'] and r['target_sha256']==q['target_sha256']
 assert q['input_receipt_sha256']==sha(receipt)
 for name,digest in r['sources'].items():assert sha(ROOT/name)==digest,name
 baseline=ROOT/'build/emulate-connection-candidate-20261107/terminal/manifest.json'
 b=json.loads(baseline.read_text());m=b['memory_layout']
 assert b['binary_sha256']=='856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7'
 names=list(r['sources'])+['standalone/prove_line_port_persist_source.py',
  'standalone/record_line_port_persistence.py','docs/LINE_PORT_PERSISTENCE.md']
 record=dict(storage_component_verified=True,real_DOS_checks=28,injected_fault_checks=37,
  application_integrated=False,physical_runtime_verified=False,installed_package_changed=False,
  source_files_in_export=len(q['sources']),sources={n:sha(ROOT/n)for n in names},
  receipts={str(p.relative_to(ROOT)):sha(p)for p in (receipt,proof,baseline)},
  baseline_memory=dict(parent_sha256=b['binary_sha256'],DGROUP_bytes=m['near_bytes'],
   DGROUP_spare=m['near_spare_bytes'],resident_code_bytes=m['resident_CS_extent_bytes'],resident_code_spare=m['resident_CS_spare_bytes']),
  limitations=['Canonical startup identity, exclusive claim and recovery/handle retirement are caller responsibilities.',
   'Live popup, PROGRAM/UART handoff, saved-baseline reconciliation and configured display integration remain open.',
   'No crash-atomic, external-concurrent-writer or physical-disk-fault guarantee; metadata is not preserved.'])
 (ROOT/'docs/validation/line-port-persistence.json').write_text(json.dumps(record,indent=2)+'\n')
 print('Recorded 28 real DOS +37 fault storage checks; live composition remains open')


if __name__=='__main__':main()
