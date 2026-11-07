#!/usr/bin/env python3
"""Bind the serviced Meta dialog, native traces and source/VGA evidence."""
import argparse,json
from pathlib import Path
from build_meta_dialog import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','vga','proof','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 build=a.build.resolve();vga=a.vga.resolve();core=load(build/'result.json');video=load(vga/'result.json');cold=load(a.proof.resolve()/'result.json')
 assert core['original_inputs']==cold['original_inputs']==[] and core['cases']==cold['cases']==328 and core['key_states']==cold['key_states']==3341
 assert core['view_checks']==3341 and core['API_guards']==8 and core['state_bytes']==684 and core['state_outside_DGROUP']
 assert core['null_guard_at_DGROUP_start'] and core['separate_code_segment'] and core['data_equals_stack'] and core['cpu']=='8086'
 assert sha(build/'METADLG.EXE')==core['binary_sha256']==cold['binary_sha256']==video['controller_sha256']
 assert sha(vga/'METAPOP.EXE')==video['demo_sha256']==cold['demo_sha256']
 assert len(video['checks'])==7 and all(video['checks'].values()) and cold['VGA_checks']==video['checks']
 assert cold['source_count']==12 and cold['ancestor_git_unavailable']
 for n,h in video['artifacts'].items():assert sha(vga/n)==h
 for n,h in video['input_objects'].items():assert sha(ROOT/n)==h
 fixture=ROOT/'standalone/fixtures/meta_dialog_native.json';native=json.loads(fixture.read_text());assert native['passed'] and native['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 assert len(native['cases'])==328 and sum(len(c['states']) for c in native['cases'])==3341
 for n in ('standalone/record_meta_dialog.py','standalone/prove_meta_dialog_source.py','standalone/capture_meta_dialog_original.py','docs/META_DIALOG.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,terminal_changed=False,installed_changed=False,physical_runtime_verified=False,
  controller_sha256=core['binary_sha256'],VGA_probe_sha256=video['demo_sha256'],cases=328,key_states=3341,view_checks=3341,API_guards=8,state_bytes=684,state_outside_DGROUP=True,VGA_checks=video['checks'],isolated_source_files=12,
  native_authority=dict(original_sha256=native['original_sha256'],dispatch_evidence=native['native_dispatch_evidence'],scope=native['scope']),sources=sources,receipts=receipts,original_inputs=[],
  limitations=['Original instruction replay uses synthetic definitions and modeled peripheral/window/file services. Authored window decoration is not original VGA equivalence.',
   'Actual source-built DOS8086 controller and passive-observed VGA probe with exact screen/cursor/shape restoration; probe file commands deliberately fail without a persistence backend.',
   'Checked KEY IO, filename selection, canonical resource/live action adoption, foreground ownership, application memory/BBS/physical acceptance and full F02/F05/F06 remain open.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta dialog receipt:328 cases,3341 states/views,8 guards,7 VGA checks,12-file source rebuild')


if __name__=='__main__':main()
