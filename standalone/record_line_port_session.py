#!/usr/bin/env python3
"""Bind accepted transaction component checks, retaining open integration gates."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-session'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 dos=json.loads((OUT/'dos-results.json').read_text())
 proof=json.loads((OUT/'source-proof/result.json').read_text())
 assert dos['passed'] and dos['checks']==71 and dos['separate_bank_segment']*16>=65536
 assert dos['binary_sha256']==manifest['binary_sha256']==sha(OUT/'SESSION.EXE')
 assert proof['passed'] and proof['dos_result']['checks']==71
 for record in (manifest,proof):
  for name,digest in record['sources'].items():assert sha(ROOT/name)==digest,name
 for name,digest in proof['exact_outputs'].items():assert sha(OUT/name)==digest,name
 names=list(proof['sources'])+['standalone/prove_line_port_session_source.py',
  'standalone/record_line_port_session.py','docs/LINE_PORT_SESSION.md']
 paths=[OUT/'manifest.json',OUT/'dos-results.json',OUT/'source-proof/result.json']
 r=dict(component_verified=True,application_integrated=False,persistence_executed=False,
  uart_apply_executed=False,physical_runtime_verified=False,installed_package_changed=False,
  dos_checks=71,popup_cells=dos['popup_cells'],isolated_source_files=len(proof['sources']),
  sources={n:sha(ROOT/n)for n in names},
  receipts={str(p.relative_to(ROOT)):sha(p)for p in paths},
  limitations=['Save/apply results are authored inputs; no real PRM save or UART handoff in this diagnostic.',
   'Terminal routes, serviced-input composition, foreground binding, configured colors and recovery reporting remain open.',
   'Exact installed RBADE091 and physical acceptance remain separate.'])
 (ROOT/'docs/validation/line-port-session.json').write_text(json.dumps(r,indent=2)+'\n')
 print('Recorded 71-check Line/Port transaction component; live integration gates remain open')


if __name__=='__main__':main()
