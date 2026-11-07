#!/usr/bin/env python3
"""Bind production EMULATE bridge/WHEN and exact-product modern BBS regressions."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={};products={}
 def bind(items):
  for name,digest in items.items():
   assert sha(ROOT/name)==digest,name
   (receipts if Path(name).parts[0]=='build' else sources)[name]=digest
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path);bind(r.get('sources',{}));return r
 for name,folder in [('TERMINAL.EXE','emulate-rpc-parent-20261107'),('ASPECT.EXE','emulate-rpc-child-checked-20261107'),('ASPCOMP.EXE','aspect-compiler-dos')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256'];bind(m['sources'])
  products[name]=m['binary_sha256'];receipts[str((root/'manifest.json').relative_to(ROOT))]=sha(root/'manifest.json')
 bridge=load('build/emulate-rpc-bridge-checked-20261107/result.json');assert bridge['parent_sha256']==products['TERMINAL.EXE'] and len(bridge['cases'])==81
 when=[]
 for folder,reject,count in [('emulate-rpc-when-success-final-20261107',False,31),('emulate-rpc-when-error-final-20261107',True,38)]:
  r=load('build/'+folder+'/result.json');assert r['binary_sha256']==products['TERMINAL.EXE'] and r['interpreter_sha256']==products['ASPECT.EXE']
  assert r['emulate_when'] and r['emulate_profile_switch'] and r['cpu']=='386' and r['exit_watch_high']
  assert len(r['checks'])==count and all(r['checks'].values())
  assert [e['error'] for e in r['exit_watch']['exits']]==([3,0,0,0] if reject else [0,0,0,0])
  root=ROOT/'build/connection-dos'/folder
  for name in ('serial.bin','SCREEN.BIN','EXITSTAT.BIN','FIRST.ASX','SIX.ASX','MISSING.ASX','EWATCH.COM'):
   receipts[str((root/name).relative_to(ROOT))]=sha(root/name)
  if reject:receipts[str((root/'REJECT.ASX').relative_to(ROOT))]=sha(root/'REJECT.ASX')
  when.append(dict(error=reject,checks=count,exit_errors=[e['error'] for e in r['exit_watch']['exits']]))
 root=ROOT/'build/bbs-lab/results/synchronet/emulate20-shared-synchronet-20261107'
 sync=load(str((root/'proxy-integration.json').relative_to(ROOT)))
 assert sync['binary_sha256']==products['TERMINAL.EXE'] and sync['interpreter_sha256']==products['ASPECT.EXE']
 assert len(sync['checks'])==25 and all(sync['checks'].values()) and sync['external_viewer']['passed'] and all(sync['external_viewer']['checks'].values())
 bind(sync['product_inputs']);bind(sync['external_viewer']['sources'])
 for n,h in sync['generated_inputs'].items():assert sha(root/n)==h,n;receipts[str((root/n).relative_to(ROOT))]=h
 load(str((root/'result.json').relative_to(ROOT)));load(str((root/'external-viewer-audit.json').relative_to(ROOT)))
 sync_screen=load(str((root/'screen-reference-audit.json').relative_to(ROOT)));assert sync_screen['matched_cells']==1920 and sync_screen['different_cells']==0
 load(str((root/'size-probe-screen-audit.json').relative_to(ROOT)))
 root=ROOT/'build/bbs-lab/results/enigma/emulate20-shared-enigma-20261107'
 enigma=load(str((root/'carrier-checks.json').relative_to(ROOT)))
 assert {n:v['sha256'] for n,v in enigma['products'].items()}==products and all(enigma['checks'].values()) and not enigma['errors']
 audit=load('build/emulate20-shared-enigma-audit-20261107/result.json');bind(audit['captures'])
 assert audit['exact_retry_bytes']==65539 and audit['terminal_sha256']==products['TERMINAL.EXE']
 for name in ('BEFORE.BIN','AFTER.BIN','SCREEN.BIN','LABELS.BIN','GEOM.BIN','PASS.TXT','program/LOGON.ASX','RECV/P24E532.BIN'):
  receipts[str((root/name).relative_to(ROOT))]=sha(root/name)
 root=ROOT/'build/bbs-lab/results/enigma/emulate20-shared-enigma-editor-20261107'
 editor=load(str((root/'proxy-integration.json').relative_to(ROOT)))
 assert editor['binary_sha256']==products['TERMINAL.EXE'] and len(editor['checks'])==9 and all(editor['checks'].values())
 bind(editor['product_inputs']);bind(editor['external_viewer']['sources'])
 assert editor['external_viewer']['passed'] and len(editor['external_viewer']['checks'])==12 and all(editor['external_viewer']['checks'].values())
 for name in ('result.json','semantic-audit.json','external-viewer-audit.json','size-probe-screen-audit.json'):
  load(str((root/name).relative_to(ROOT)))
 editor_screen=load(str((root/'screen-reference-audit.json').relative_to(ROOT)));assert editor_screen['matched_cells']==1920 and editor_screen['different_cells']==0
 for name in ('SCREEN.BIN','GEOM.BIN'):
  receipts[str((root/name).relative_to(ROOT))]=sha(root/name)
 for name in ('standalone/record_aspect_emulate_integration.py','standalone/check_aspect_emulate_bridge.py'):
  sources[name]=sha(ROOT/name)
 report=dict(passed=True,release_accepted=False,installed_changed=False,products=products,sources=sources,receipts=receipts,original_inputs=[],
  summary=dict(linked_bridge_cases=81,WHEN_DOS=when,Synchronet_checks=25,Synchronet_exact_cells=1920,Synchronet_different_cells=0,Synchronet_external_viewer_checks=len(sync['external_viewer']['checks']),Enigma_checks=len(enigma['checks']),Enigma_independent_audit=True,Enigma_exact_retry_bytes=audit['exact_retry_bytes'],Enigma_parent_editor_checks=9,Enigma_parent_editor_external_checks=12,Enigma_parent_editor_exact_cells=1920,Enigma_parent_editor_different_cells=0),
  limitations=['Production parent bridge executes against authored child frames and modeled DOS/UART/BIOS/MCB/filesystem boundaries. This is not full real EXEC/IRQ fault composition.',
   'WHEN tests execute actual normal parent/interpreter/native opcode with synthetic peer and passive UMB observer; deferred registration/worker/main wire order and exit owners are checked, not all WHEN internals or timing.',
   'Synchronet editor/external viewer and Enigma DCD/redial/transfer use isolated serial/Telnet proxy paths and stock owned servers. No SIP/DSP/audio/analog/physical acceptance claim.',
   'The separate Enigma editor workflow exercises the parent with keyboard-driven login; no ASPECT interpreter runs in that editor fixture. The carrier/retry workflow separately tests the full parent/interpreter/compiler pair.',
   'Native fatal-reset/abort expansion, sustained receive latency during keyboard import/reset, matched capability20 package/compiler reproduction and physical acceptance remain open. No full original feature parity or deployment claim.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE production integration',report['summary'])
if __name__=='__main__':main()
