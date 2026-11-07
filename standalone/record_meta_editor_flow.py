#!/usr/bin/env python3
"""Bind composed Meta workflow, actual VGA, native regression and source export."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','vga','native','proof','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 core=load(a.build.resolve()/'result.json');vga=load(a.vga.resolve()/'result.json');native=load(a.native.resolve()/'result.json');cold=load(a.proof.resolve()/'result.json')
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and core['logs']==cold['logs']
 assert 'PASS 3069 checks;state 12870;' in core['logs']['NORMAL.LOG'] and 'PASS fatal 981 checks;' in core['logs']['FATAL.LOG']
 assert sha(a.build.resolve()/'METAEDIT.EXE')==core['binary_sha256']==cold['binary_sha256']==vga['controller_sha256']
 assert sha(a.vga.resolve()/'METAVGA.EXE')==vga['demo_sha256']==cold['demo_sha256'] and len(vga['checks'])==9 and all(vga['checks'].values()) and cold['VGA_checks']==vga['checks']
 assert sha(a.native.resolve()/'METADLG.EXE')==native['binary_sha256']==cold['native_binary_sha256'] and native['cases']==cold['native_cases']==328 and native['key_states']==cold['native_states']==3341 and native['API_guards']==8
 assert cold['source_count']==53 and cold['ancestor_git_unavailable'] and core['editor_owned_DGROUP_bytes']==0
 for n,h in vga['input_objects'].items():assert sha(ROOT/n)==h
 for n in ('standalone/record_meta_editor_flow.py','standalone/prove_meta_editor_bundle_source.py','standalone/prove_meta_editor_flow_source.py','docs/META_EDITOR_FLOW.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],VGA_probe_sha256=vga['demo_sha256'],native_dialog_sha256=native['binary_sha256'],normal_assertions=3069,fatal_assertions=981,state_bytes=12870,editor_owned_DGROUP_bytes=0,editor_owned_segments=core['editor_owned_segments'],VGA_checks=vga['checks'],native_cases=328,native_states=3341,native_guards=8,isolated_source_files=53,original_inputs=[],sources=sources,receipts=receipts,
 limitations=['Actual DOS workflow and VGA probe over synthetic owned files, with explicit admission supplied by the test caller. No connected UART/terminal handoff or live adoption occurs.', 'Actual VGA frames/restoration and exact saved KEY/proposal bytes; authored decoration, not original pixel equivalence. Native-reference regression uses existing frozen dispatcher/field traces with modeled peripherals.', 'Matched transient module, resident services, modal/menu/Alt-M hooks, global EXEC/file admission and atomic live action commit, parent memory/capacity/UART/BBS/physical acceptance remain open. Fatal paths must retain lease code/state until DOS exit. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS composed editor receipt:3069/981 assertions,9 VGA checks,3341 native states,53-file source rebuild')
if __name__=='__main__':main()
