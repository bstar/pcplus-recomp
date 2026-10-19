#!/usr/bin/env python3
"""Bind filename UI checks to the frozen DOS binary and observed ENiGMA run."""
import hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 label='owned-game-labels-01';base='build/bbs-lab/results/enigma/'+label
 binary=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==binary
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 paths={'UI':'build/terminal/zmodem-name-ui-checks.json','workflows':'build/terminal/terminal-zmodem-live-checks.json',
  'owners':'build/terminal/zmodem-owners-live-checks.json','far_ABI':'build/terminal/config-far-checks.json',
  'normal_DOS':'build/terminal-tests/normal/result.json','DOS':base+'/repeat-checks.json','negative_audit':base+'/audit-negative-checks.json'}
 reports={}
 for key,p in paths.items():
  d=read(p);assert d['passed'],p
  if key=='negative_audit':assert len(d['cases'])==7 and all(c['rejected'] for c in d['cases'])
  else:assert d.get('binary_sha256',d.get('terminal_sha256'))==binary,p
  reports[key]=dict(path=p,sha256=sha(p))
 ui=read(paths['UI']);assert ui['inputs']==17 and ui['checker_sha256']==sha('standalone/check_zmodem_name_ui.py')
 dos=read(paths['DOS']);assert all(dos['checks'].values()) and not dos['errors']
 assert dos['checks']['actual_DOS_save_skip_save_labels']
 assert dos['input_hashes']['terminal']==dos['input_hashes']['staged_terminal']==binary
 for k,p in [('runner','lab/bbs/enigma_repeat_download_dos.py'),('harness','lab/bbs/test_dos.py'),('observer','lab/bbs/test_transfer_dos.py'),('label_observer','lab/bbs/zmodem_label_watch.py'),('auditor','lab/bbs/audit_zmodem.py')]:assert dos['input_hashes'][k]==sha(p),p
 neg=read(paths['negative_audit']);assert neg['checker_sha256']==sha('lab/bbs/check_enigma_repeat_audit.py') and neg['auditor_sha256']==sha('lab/bbs/enigma_repeat_download_dos.py')
 for p,h in neg['capture_hashes'].items():assert sha(base+'/'+p)==h,p
 # Bind the actual assembled independent observer, including the imported
 # canonical hardware sampler, rather than just its small adapter module.
 sys.path[:0]=[str(ROOT/'standalone'),str(ROOT/'lab/bbs')]
 from zmodem_label_watch import SAMPLER
 sampler=SAMPLER
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x2f8+off))
 assert (ROOT/base/'sampler.asm').read_text()==sampler
 raw=(ROOT/base/'LABELS.BIN').read_bytes();assert len(raw)==2566
 magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4e5a and 0<count<=16 and ticks
 frames=[raw[6+i*160:6+(i+1)*160] for i in range(count)]
 assert [f[::2].decode('cp437') for f in frames]==dos['observed_labels']
 assert [t['kind'] for t in dos['transactions']]==['received','skipped-existing','received']
 first,second=dos['local_names'];snapshots=dos['snapshots'];assert len(snapshots)==3
 assert [set(s['files']) for s in snapshots]==[{first},{first},{first,second}]
 assert snapshots[0]['files'][first]==snapshots[1]['files'][first]==snapshots[2]['files'][first]
 for wire,local in zip(dos['wire_names'],dos['local_names']):assert sha(base+'/RECV/'+local)==snapshots[2]['files'][local]['sha256']
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==binary
 assert 'standalone/check_zmodem_name_ui.py' in proof['build_scripts']
 assert read('build/dos-package/manifest.json')['files']['TERMINAL.EXE']==binary
 live=ROOT.parent/'black-flag-bbs'
 live_modules={p:hashlib.sha256((live/p).read_bytes()).hexdigest() for p in dos['source_modules']}
 assert live_modules==dos['source_modules'],'Owned source changed; review the isolated fixture before making current-source claims'
 live_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=live,text=True).strip()
 live_client=hashlib.sha256((live/'core/client.js').read_bytes()).hexdigest()
 assert live_client=='d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788'
 result=dict(passed=True,terminal_sha256=binary,reports=reports,linked_cases=ui['inputs'],
  DOS=dict(checks=dos['checks'],observed_labels=dos['observed_labels'],transactions=[dict(kind=t['kind'],wire_name=t['wire_name'],local_name=t['local_name']) for t in dos['transactions']],existing_file_identity_preserved=True),
  independent_sampler=dict(source_sha256=sha('lab/bbs/zmodem_label_watch.py'),base_source_sha256=sha('standalone/test_terminal.py'),assembled_source_sha256=sha(base+'/sampler.asm'),program_sha256=sha(base+'/SNAP.COM'),capture_sha256=sha(base+'/LABELS.BIN'),frames=count,matching_timer_samples=ticks),
  source_build=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),memory_layout=manifest['memory_layout'],data_stack_bytes=manifest['data_stack_bytes'],
  source_modules=dos['source_modules'],runtime_sources={p:sha(p) for p in ('src/transfer/terminal_zmodem.c','src/terminal/transfer_ui.asm')},recorder_sha256=sha(Path(__file__).relative_to(ROOT)),
  live_source_recheck=dict(revision=live_revision,client_sha256=live_client,selected_modules_match_fixture=True),
  live_server_modified=False,whole_application_gates_closed=[],
  scope='Current DOS application displays wire/local name on its owned transfer footer, with Save/Skip distinction and bounded remote truncation. Linked engine/storage/video restoration plus independent actual DOS INT1C label capture during one ENiGMA receive/skip/receive connection. Source-only reconstruction remains incomplete.',
  limitations=['Remote footer field is46 columns, with a trailing tilde on truncation; engine identity remains up to255 bytes.',
   'No persistent remote/local catalog or automatic hash-collision renaming; existing targets still explicitly skip.',
   'Isolated selected owned ENiGMA sources/menus/art with generated archives and modeled19200/HARD modem. Live decoder installation and physical modem remain untested.'])
 (ROOT/'docs/validation/zmodem-name-ui.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded linked and actual DOS ENiGMA filename display, checked skip, screen restoration and source-only build')
if __name__=='__main__':main()
