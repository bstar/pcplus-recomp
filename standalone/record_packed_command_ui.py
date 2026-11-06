#!/usr/bin/env python3
"""Bind lossless UI packing to unchanged runner capacity and composed compatibility."""
import argparse,json,struct
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=ROOT/'build/editor-packed-ui-v3-20261106/TERMINAL.EXE';digest=sha(binary)
 manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert manifest['binary_sha256']==digest and manifest['experimental_packed_command_ui']
 assert manifest['experimental_external_editor']
 def bind(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def read(path,product=True):
  r=json.loads(path.read_text());assert r['passed'],path
  if product:assert r['binary_sha256']==digest,path
  for n,h in r.get('sources',r.get('product_inputs',{})).items():assert sha(ROOT/n)==h,n
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  return r
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 packed=manifest['packed_command_ui'];assert packed['literals']==230 and packed['pairs']==64 and packed['max_depth']==3
 assert packed['original_literal_bytes']==12738 and packed['packed_literal_bytes']==7972
 folder=binary.parent
 assert sha(folder/'command_menu_packed.c')==packed['generated_sha256'] and sha(folder/'command_ui_pairs.h')==packed['dictionary_sha256']
 memory=manifest['memory_layout'];assert memory['near_bytes']==65488 and memory['resident_code_bytes']==65516
 assert memory['minimum_allocated_module_bytes']==478656
 assert (30195-memory['retained_parent_paragraphs'])*16==4224
 frames_path=ROOT/'build/packed-ui-frame-parity-v3-20261106/result.json';frames=read(frames_path)
 assert frames['identical_frames']==1146 and len(frames['cases'])==1146
 proof_path=ROOT/'build/packed-ui-public-source-proof-v2-20261106/result.json';proof=read(proof_path)
 assert proof['disabled_sha256']=='93f08d0cf3fd4174718e7ca727758ddb63f4e6f0ecd1471b3fb00c41c1f4d800' and not proof['original_inputs'] and proof['ancestor_git_unavailable']
 layout_path=ROOT/'build/packed-ui-v3-layout-20261106/result.json';layout=read(layout_path)
 assert layout['state_bytes']==130 and len(layout['negative_controls'])==5 and all(c['rejected'] for c in layout['negative_controls'])
 modal=[]
 for tool,names in [('editor',['relative','absolute','options','spaces','empty','cancel','long','maximum','reference','browser','malformed','disabled']),('viewer',['relative','options','cancel','reference','browser','maximum'])]:
  for name in names:
   path=ROOT/f'build/packed-ui-v3-{tool}-{name}-20261106/result.json';r=read(path)
   assert r['tool']==tool and len(r['cases'])==1 and all(r['cases'][0]['checks'].values())
   modal.append(dict(tool=tool,case=name,report=bind(path)))
 servers=[]
 for server,label in [('synchronet','packed-ui-v3-sync-20261106'),('enigma','packed-ui-v3-enigma-20261106')]:
  path=ROOT/'build/bbs-lab/results'/server/label/'proxy-integration.json';r=read(path)
  child=r['external_viewer'];assert child['passed'] and child['external_command_tool']=='editor' and all(child['checks'].values())
  audit_path=path.with_name('screen-reference-audit.json');audit=read(audit_path)
  assert audit['matched_cells']==1920 and audit['different_cells']==0
  for capture,h in audit['captures'].items():assert sha(Path(capture))==h,capture
  servers.append(dict(server=server,report=bind(path),reference=bind(audit_path),matched_cells=1920,different_cells=0))
  if server=='synchronet':
   assert r['interpreter_sha256']=='23caac9350b0a4be6f5898ce4bbc52c21604a5410a5f3340feae7732e04b004f'
   raw=(path.parent/'ADMIT.BIN').read_bytes();assert len(raw)==102
   words=struct.unpack_from('<19H',raw)
   assert words[18]==0 and words[14]>0 and not words[15]&1 and words[17] in (0x3d00,0x6c00)
   servers[-1]['successful_script_open_witness']=bind(path.parent/'ADMIT.BIN')
 streams_path=ROOT/'build/packed-ui-v3-six-streams-20261106/result.json';streams=read(streams_path)
 assert streams['interpreter_sha256']=='23caac9350b0a4be6f5898ce4bbc52c21604a5410a5f3340feae7732e04b004f'
 assert streams['checks']['all_six_streams'] and streams['checks']['six_files'] and streams['checks']['four_calls']
 transfers_path=ROOT/'build/packed-ui-v3-transfers-20261106/result.json';transfers=read(transfers_path)
 assert transfers['external_command_tool']=='editor' and len(transfers['cases'])==6
 for c in transfers['cases']:assert c['passed'] and c['terminal_sha256']==digest and all(c['checks'].values())
 retry=next(c for c in transfers['cases'] if c['case']=='y-rx-cancel-retry')
 assert all(retry['checks'][k] for k in ['actual_CAN_pair','cancelled_and_resumed_before_retry','retry_completed_same_connection'])
 loss=[]
 for name in ['child-loss','transfer-loss']:
  path=ROOT/f'build/packed-ui-v3-{name}-20261106/result.json';r=read(path)
  assert r['external_command_tool']=='editor' and len(r['cases'])==2
  for c in r['cases']:assert c['passed'] and all(c['checks'].values()) and c['checks']['two_actual_connections']
  loss.append(bind(path))
 result=dict(passed=True,binary_sha256=digest,retained_module_bytes=478656,retained_parent_paragraphs=memory['retained_parent_paragraphs'],
  saved_against_editor_bytes=4224,saved_against_reviewed_viewer_bytes=3744,near_bytes=65488,resident_code_bytes=65516,
  packed_text=packed,UI_comparison=bind(frames_path),public_source_build=bind(proof_path),source_commit=proof['source_commit'],
  linked_layout=bind(layout_path),modal_workflows=modal,servers=servers,stream_capacity=bind(streams_path),
  transfers=bind(transfers_path),carrier_recovery=loss,interpreter_changed=False,default_interpreter_heap_growth=512,
  installed_package_changed=False,sources={'standalone/record_packed_command_ui.py':sha(Path(__file__))},
  limits=['Uncompressed UI control and packed variant both correct the category far-pointer conversion; comparison is not against the prior corrupted category display.',
   'Final v3 BBS sessions run sequentially; earlier v2 concurrent Enigma session failed semantics and is excluded, not reattributed to the category fix.',
   'Software-only DOS/loopback BBS tests; physical Boca/SPA2102/SIP/audio/CTS acceptance and complete original parity remain open.',
   'Nested ASPECT PROGRAM composition remains a separate open gate; no stack,history,stream capacity or command is removed.',
   'Default uncompressed/editor-off reviewed package recipe and installed selection are not updated by this receipt.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS4224 bytes recovered,1146 exact frames,18 modals,2 BBSes,6 streams,6 transfers,4 recovery cases and public rebuild')
if __name__=='__main__':main()
