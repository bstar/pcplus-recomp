#!/usr/bin/env python3
"""Reconcile the frozen live ZMODEM checkpoint without rewriting older ledgers."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--small',required=True);p.add_argument('--large-first',required=True);p.add_argument('--large-retry',required=True);a=p.parse_args()
 manifest=read('build/terminal/manifest.json');runtime=manifest['binary_sha256'];memory=manifest['memory_layout']
 assert sha('build/terminal/TERMINAL.EXE')==runtime
 for path,digest in manifest['sources'].items():assert sha(path)==digest,path
 assert memory['near_bytes']==65056 and memory['resident_code_bytes']==62946
 assert memory['configuration_bridge_pairs_verified']==66 and memory['far_code_bridge_pairs_verified']==115
 assert memory['zmodem_far_callbacks_verified']==10
 cpu=read('build/terminal/terminal-zmodem-live-checks.json');owners=read('build/terminal/zmodem-owners-live-checks.json');frames=read('build/terminal/config-far-checks.json')
 for d in (cpu,owners,frames):assert d['passed'] and d['binary_sha256']==runtime
 assert cpu['inputs']==38 and owners['inputs']==10 and len(frames['rejected_mutations'])==325
 assert cpu['test_sha256']==sha('standalone/check_terminal_zmodem_live.py') and owners['test_sha256']==sha('standalone/check_zmodem_owners_live.py')
 regression=read('build/terminal/setup-profile-regression.json');commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==78 and regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert commands==[c['command'] for c in regression['commands']] and all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==64 and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==runtime
 for name,d in proof['outputs'].items():assert d['matches_workspace'] and sha(Path('build')/name)==d['sha256'],name
 assert read('docs/validation/terminal-source-build.json')['manifest']==manifest
 baseline=json.loads(subprocess.check_output(['git','show','ade39f3:docs/validation/terminal-source-build.json'],cwd=ROOT))['manifest']
 assert memory['near_bytes']-baseline['memory_layout']['near_bytes']==336
 assert memory['resident_code_bytes']-baseline['memory_layout']['resident_code_bytes']==724
 storage={n:read(n) for n in ['build/upload-file/checks.json','build/upload-file/manifest.json','build/batch-upload/checks.json','build/batch-download/result.json']}
 for name,d in storage.items():
  if 'passed' in d:assert d['passed'],name
  for path,digest in d.get('sources',{}).items():assert sha(path)==digest,(name,path)
 artifacts=list(map(Path,['build/terminal/manifest.json','build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/terminal/terminal-zmodem-live-checks.json','build/terminal/zmodem-owners-live-checks.json','build/terminal/config-far-checks.json','build/terminal/setup-profile-regression.json','build/application-source-proof/snapshot.json','build/application-source-proof/build.log','build/application-source-proof/result.json']))
 artifacts.extend(map(Path,storage))
 dos={};peer_hashes={}
 for key,label in [('small',a.small),('large_first',a.large_first),('large_retry',a.large_retry)]:
  assert label.replace('-','').replace('_','').isalnum();folder=Path('build/terminal-zmodem-dos')/label;report=read(folder/'checks.json')
  assert report['binary_sha256']==runtime
  if key!='large_first':assert report['passed']
  for c in report['cases']:
   where=folder/c['case'];assert read(where/'result.json')==c and c['binary_sha256']==runtime
   if c['passed']:
    assert all(c['checks'].values()) and c['peer_exit']==0
    assert (ROOT/where/'BEFORE.BIN').read_bytes()==(ROOT/where/'AFTER.BIN').read_bytes() and (ROOT/where/'BEFORE.BIN').stat().st_size==42
    for name,digest in c['files'].items():
     for part in (('SEND','PEER') if c['case'].startswith('tx-') else ('PEER','RECV')):assert sha(where/part/name)==digest
   command=c.get('peer_command')
   if command:peer_hashes[command[0]]=sha(command[0])
  artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT/folder).rglob('*')) if p.is_file());dos[key]=report
 assert {c['case'] for c in dos['small']['cases']}=={'rx-default','rx-crc16','tx-default','tx-escape'}
 assert {c['case'] for c in dos['large_first']['cases'] if c['passed']}=={'rx-default','rx-crc16'}
 assert {c['case'] for c in dos['large_first']['cases'] if not c['passed']}=={'tx-default','tx-escape'}
 assert {c['case'] for c in dos['large_retry']['cases']}=={'tx-default','tx-escape'}
 inputs=['standalone/record_live_zmodem.py','standalone/build_terminal.py','standalone/terminal_memory.py','standalone/check_config_far_live.py','standalone/check_terminal_zmodem_live.py','standalone/check_zmodem_owners_live.py','standalone/test_terminal_zmodem_dos.py','standalone/check_zmodem.py','standalone/check_zmodem_wire.py','standalone/check_terminal_ymodem_live.py','standalone/check_terminal_transfer_live.py','standalone/check_terminal_upload_live.py','standalone/test_terminal.py','standalone/test_terminal_transfer_dos.py','standalone/test_terminal_ymodem_dos.py','standalone/prove_source_build.py','nix/flake.nix','nix/flake.lock','Makefile']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=memory,published_baseline=dict(commit='ade39f34d9f5fe7cc02f451ed5faa331c652a454',manifest=baseline),
  linked=cpu,unresolved_owners=owners,call_frames=frames,storage_components=storage,actual_DOS=dos,peer_binaries=peer_hashes,terminal_regression=regression,
  source_rebuild=dict(output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256'],report='docs/validation/application-components-source-build.json'),
  runtime_sources=manifest['sources'],sources={n:sha(n) for n in inputs},retained_artifacts={str(n):sha(n) for n in sorted(set(artifacts))},
  scope='Live source-built ZMODEM entry, CONFIG_CODE codec/engine/adapter and ten exact far callback identities/relocations; checked source seek/skip and variable receive writes, serviced UART and F2 UI.38 linked workflows,10 unresolved-owner guards,325 damaged frames/pointers,78 terminal commands and64 source-only byte-identical outputs. Eight successful actual DOS lrzsz workflows plus two retained failed initial large-upload fixture attempts. Logged-in stock BBS, full recovery/timing matrix, physical modem, full original streaming/auto-download/UI and whole-application completion remain open.')
 (ROOT/'docs/validation/live-zmodem.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded live ZMODEM',runtime,len(result['retained_artifacts']),'artifacts')
if __name__=='__main__':main()
