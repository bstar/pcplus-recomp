#!/usr/bin/env python3
"""Bind source-owned command UI to linked/DOS/regression/source-only evidence."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from check_setup_model import image
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sources(report):
 for p,h in report.get('sources',{}).items():assert sha(p)==h,p
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 runtime=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json');sources(manifest)
 assert manifest['binary_sha256']==runtime
 linked=read('build/terminal/command-menu-checks.json');dos_path=Path('build/command-menu-dos')/a.label/'checks.json';dos=read(dos_path)
 for r in (linked,dos):assert r['passed'] and r['binary_sha256']==runtime;sources(r)
 assert linked['inputs']==153 and len(linked['cases'])==5 and len(dos['cases'])==4
 assert dos['editor_sha256']==sha('build/setup/PRMEDIT.EXE')
 artifacts=[dos_path,Path('build/terminal/command-menu-checks.json'),Path('build/terminal/manifest.json')]
 for i,case in enumerate(dos['cases']):
  assert case['passed'] and all(case['checks'].values())
  base=Path('build/setup-startup') if i==2 else Path('build/connection-dos')
  folder=base/case['case'];before=(ROOT/folder/'BEFORE.BIN').read_bytes()
  assert len(before)==42 and before==(ROOT/folder/'AFTER.BIN').read_bytes()
  wire=(ROOT/folder/'serial.bin').read_bytes();assert b'ready' in wire
  if i==0:
   raw=(ROOT/folder/'MVIEW.BIN').read_bytes();assert len(raw)==10246
   magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4d43 and 0<count<=32 and ticks>5
   frames=[raw[6+n*320:6+(n+1)*320] for n in range(count)]
   assert [f.decode('cp437') for f in frames]==case['observed_frames']
   for text in (b'Receive files',b'Dial selected target',b'Redisplay history',b'Browse a frozen',b'Drain outgoing'):
    assert any(text in f for f in frames),text
   assert b'interval' not in wire and b'\x1b[C' not in wire and b'\x1b[5;11R' in wire
  elif i==1:
   assert (ROOT/folder/'PCPLUS.LOG').read_bytes()==b'CAPTURELINE\r\n'
   snapshot=(ROOT/folder/'PCPLUS.SCR').read_bytes()
   assert b'CAPTURELINE' in snapshot and b'Command Menu' not in snapshot and b'Receive files' not in snapshot
   assert wire.count(b'ATZ\r')==wire.count(b'ATDCaseTest:23\r')==2 and b'+++ATH\r' in wire
   assert b'\x15' not in wire and b'\x18' not in wire
  elif i==2:
   assert sha(folder/'TERMINAL.EXE')==runtime and sha(folder/'PRMEDIT.EXE')==dos['editor_sha256']
   assert (ROOT/folder/'TEST.PRM').read_bytes()==image()
  else:
   raw=(ROOT/folder/'MVIEW.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',raw)
   assert len(raw)==10246 and magic==0x4d43 and 0<count<=32 and ticks>5
   frames=[raw[6+n*320:6+(n+1)*320] for n in range(count)]
   assert [f.decode('cp437') for f in frames]==case['observed_frames']
   assert any(b'Redisplay history' in f[:80] for f in frames)
   assert b'\x1b[C' not in wire and b'\x1b[2;1R' in wire
  artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT/folder).rglob('*')) if p.is_file())
 artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT/dos_path.parent).iterdir()) if p.is_file())
 memory=manifest['memory_layout'];assert memory['command_menu_far_code_verified']
 assert memory['far_code_bridge_pairs_verified']==110 and memory['configuration_bridge_pairs_verified']==61
 assert memory['near_bytes']==64720 and memory['resident_code_bytes']==62222
 pending=read('build/terminal/menu-pending-checks.json');assert pending['passed'] and pending['binary_sha256']==runtime and pending['inputs']==36
 sources(pending);artifacts.append(Path('build/terminal/menu-pending-checks.json'))
 frames=read('build/terminal/config-far-checks.json');assert frames['passed'] and frames['binary_sha256']==runtime and len(frames['rejected_mutations'])==276
 regression=read('build/terminal/setup-profile-regression.json');commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==77 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert commands==[r['command'] for r in regression['commands']] and all(r['exit_code']==0 for r in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime and proof['outputs']['terminal/TERMINAL.EXE']['matches_workspace']
 artifacts.extend(map(Path,['build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json']))
 stock_path='docs/validation/bbs-clipboard-transfers.json';stock=read(stock_path)
 assert stock['binary_sha256']==runtime and stock['latest_selected_workflows_passed']
 for server in ('synchronet','enigma'):
  selected=next(row for row in stock['runs'] if row['server']==server and row['label']==stock['latest_selected_workflows'][server])
  assert selected['result']['passed'] and selected['clipboard_selection']['command_menu_View_F_handoff']
 editors_path='docs/validation/bbs-editors.json';editors=read(editors_path)
 packet_path='docs/validation/bbs-enigma-packetization.json';packet=read(packet_path)
 assert editors['binary_sha256']==packet['binary_sha256']==runtime
 assert editors['servers']['synchronet']['semantic_evidence']['passed'] and packet['buffered_editor_passed']
 artifacts.extend(map(Path,[stock_path,editors_path,packet_path]))
 result=dict(passed=True,binary_sha256=runtime,linked=linked,pending_entry=pending,actual_DOS=dos,memory_layout=memory,
  call_frames=frames,terminal_regression=regression,runtime_sources=manifest['sources'],
  sources={p:sha(p) for p in ['standalone/record_command_menu.py','standalone/check_setup_model.py']},
  retained_artifacts={str(p):sha(p) for p in artifacts},
  source_rebuild=dict(report='docs/validation/application-components-source-build.json',output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256']),
  stock_BBS=dict(report=stock_path,latest_selected_workflows=stock['latest_selected_workflows'],
   selected_menu_clipboard_downloads_passed=True,all_recorded_attempts_passed=stock['all_recorded_runs_passed']),
  stock_editor_regression=dict(report=editors_path,synchronet_passed=True,
   enigma_immediate_passed=packet['immediate_editor_passed'],enigma_buffered_passed=packet['buffered_editor_passed'],packetization_report=packet_path),
  scope='Maintained Alt-Z command menu,20 items/five groups, contextual topic help and31-character ASCII prose search. Shared live/frozen screen owner and existing-command dispatch after close.153 menu and36 pending-entry linked inputs, four actual DOS observer/file/PRMEDIT/partial-CSI workflows;77-command terminal regression and64 byte-identical source-only outputs. Original layout/mouse/full settings, other geometries and physical modem remain open; no whole-application gate is closed.')
 (ROOT/'docs/validation/command-menu.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded command menu',runtime)
if __name__=='__main__':main()
