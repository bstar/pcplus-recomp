#!/usr/bin/env python3
"""Bind the windowed sender DOS/BBS checkpoint; preserve historical ledgers and failures."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
RUNTIME='d791eb10d984ec69348fa7815da8516cf38eca16161fe83345a76934ea0711d3'
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def source_check(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path

def main():
 manifest=read('build/terminal/manifest.json');m=manifest['memory_layout']
 assert manifest['binary_sha256']==sha('build/terminal/TERMINAL.EXE')==RUNTIME
 source_check(manifest)
 assert (m['near_bytes'],m['resident_code_bytes'],m['retained_parent_paragraphs'])==(65088,63038,20393)
 baseline=json.loads(subprocess.check_output(['git','show','b03ca31:docs/validation/terminal-source-build.json'],cwd=ROOT))['manifest']
 assert [m[k]-baseline['memory_layout'][k] for k in ('near_bytes','resident_code_bytes','retained_parent_paragraphs')]==[0,0,70]
 artifacts=set()
 def retain(path):
  path=Path(path)
  if (ROOT/path).is_dir():artifacts.update(p.relative_to(ROOT) for p in (ROOT/path).rglob('*') if p.is_file() and p.name!='.lock')
  else:assert (ROOT/path).is_file(),path;artifacts.add(path)
 components={}
 for name in ('wire','session','dos'):
  path=f'build/zmodem-{name}/checks.json';d=read(path);assert d['passed'];source_check(d);components[name]=d;retain(path)
 assert components['wire']['host_checks']==5051 and components['wire']['DOS_streams']==79
 assert components['session']['scripted_checks']==92 and len(components['session']['independent_peers'])==24
 assert components['dos']['DOS_cases']==61 and components['dos']['isolated_source_build_byte_identical']
 for peer in components['session']['independent_peers']:
  assert peer['passed'] and sha(peer['command'][0])==peer['peer_sha256']
  for path,digest in peer['retained_wire_sha256'].items():assert sha(path)==digest;retain(path)
 linked={}
 for name,path in [('workflows','terminal-zmodem-live-checks.json'),('owners','zmodem-owners-live-checks.json'),('frames','config-far-checks.json')]:
  file='build/terminal/'+path;d=read(file);assert d['passed'] and d['binary_sha256']==RUNTIME
  if 'test_sha256' in d:assert d['test_sha256']==sha('standalone/'+('check_terminal_zmodem_live.py' if name=='workflows' else 'check_zmodem_owners_live.py'))
  linked[name]=d;retain(file)
 assert linked['workflows']['inputs']==78 and linked['owners']['inputs']==10 and len(linked['frames']['rejected_mutations'])==325
 regression=read('build/terminal/setup-profile-regression.json')
 commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==78 and regression['complete'] and regression['passed'] and regression['binary_sha256']==RUNTIME
 assert [r['command'] for r in regression['commands']]==commands and all(r['exit_code']==0 for r in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==64 and read('docs/validation/terminal-source-build.json')['manifest']==manifest
 for path,d in proof['outputs'].items():assert d['matches_workspace'] and sha('build/'+path)==d['sha256'],path
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==RUNTIME
 for path in ('build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/terminal/manifest.json','build/terminal/setup-profile-regression.json','build/application-source-proof/snapshot.json','build/application-source-proof/result.json','build/application-source-proof/build.log'):retain(path)
 dos=read('build/terminal-zmodem-dos/window-large-d791/checks.json');assert dos['passed'] and dos['binary_sha256']==RUNTIME
 for case in dos['cases']:
  where=Path('build/terminal-zmodem-dos/window-large-d791')/case['case']
  assert case['passed'] and all(case['checks'].values()) and read(where/'result.json')==case
  assert (ROOT/where/'BEFORE.BIN').read_bytes()==(ROOT/where/'AFTER.BIN').read_bytes()
  sending=case['case'].startswith('tx')
  expected={name:(ROOT/where/('SEND' if sending else 'PEER')/name).read_bytes() for name in case['files']}
  for name,data in expected.items():assert (ROOT/where/('PEER' if sending else 'RECV')/name).read_bytes()==data and hashlib.sha256(data).hexdigest()==case['files'][name]
  audit=audit_batch((ROOT/where/('serial.bin' if sending else 'peer.bin')).read_bytes(),expected)
  lengths=[p['length'] for f in audit['files'] for p in f['packets']]
  if sending:
   assert max(lengths)<=1024 and {104,105,106,107}<={p['ending'] for f in audit['files'] for p in f['packets']}
  else:assert max(lengths)==8192
  for f in audit['files']:f.pop('source')
  destination=ROOT/where/'protocol-source-audit.json'
  if destination.exists():assert json.loads(destination.read_text())==audit
  else:destination.write_text(json.dumps(audit,indent=2)+'\n')
 retain('build/terminal-zmodem-dos/window-large-d791')
 required={('synchronet','download'):'zmodem-window-download-d791-sync-1',('synchronet','upload'):'zmodem-window-d791-sync-1',('enigma','download'):'zmodem-window-download-d791-enigma-1',('enigma','upload'):'zmodem-window-d791-enigma-1'}
 failed_stages={'zmodem-window-f6db-enigma-1':'Successful protocol/file receipt remained in the upload-details form; the form fixture was subsequently corrected. Original failed result is retained.'}
 runs=[];selected=[]
 for path in sorted((ROOT/'build/bbs-lab/results').glob('*/zmodem-window-*/result.json')):
  where=path.parent.relative_to(ROOT);d=read(where/'result.json');label=d['label'];retain(where)
  row={k:d[k] for k in ('passed','standard_completion','name','label','mode','binary_sha256','payload_sha256','checks','errors','serial')}
  if not d['passed']:assert label in failed_stages;row['failed_stage']=failed_stages[label]
  if label==required.get((d['name'],d['mode'])):
   assert d['passed'] and d['standard_completion'] and d['binary_sha256']==RUNTIME and all(d['checks'].values())
   argv=read('build/bbs-lab/'+label+'-command.json');retain('build/bbs-lab/'+label+'-command.json')
   expected={}
   for i,arg in enumerate(argv):
    if arg=='--file':
     name,source=argv[i+1].split('=',1);expected[name]=(ROOT/source).read_bytes();retain(source)
   assert {n:hashlib.sha256(v).hexdigest() for n,v in expected.items()}==d['payload_sha256']
   direction='bbs' if d['mode']=='download' else 'dos'
   stream=(ROOT/where/('display.bin' if direction=='bbs' else 'serial-received.bin')).read_bytes()
   opposite=(ROOT/where/('serial-received.bin' if direction=='bbs' else 'display.bin')).read_bytes()
   trace=read(where/'trace.json');audit=audit_batch(stream,expected)
   end_time=timestamp(trace,direction,audit['end']-1)
   after=offset_after(trace,'dos',end_time);assert after is not None
   keyboard=(ROOT/where/'serial-received.bin').read_bytes()
   post=bytes.fromhex(argv[argv.index('--post-input-hex')+1]);at=keyboard.find(post,after);assert at>=0
   audit['controls']=audit_controls(audit,opposite,trace,direction,timestamp(trace,'dos',at))
   for f in audit['files']:
    data=f.pop('source');assert (ROOT/where/('RECV' if d['mode']=='download' else 'SEND')/f['name']).read_bytes()==data
   assert audit==read(where/'protocol.json'),label
   row['protocol']=audit
   if d['mode'] in ('upload','download'):
    metadata=read(where/('server-audit.stdout' if d['mode']=='upload' else 'server-source-metadata.json'));assert metadata['passed'] and all(metadata['checks'].values())
    row['official_metadata']=metadata
   if d['name']=='enigma':
    session=read(where/'server-session-audit.json');assert session['passed'] and all(session['checks'].values());row['server_session']=session
   else:
    quota=read(str(where)+'-logon.json');assert quota['restored'] and quota['before']==quota['after']==0 and quota['level']==50
    row['quota_fixture']=quota;retain(str(where)+'-logon.json')
   selected.append(label)
  runs.append(row)
 assert len(runs)==8 and sum(r['passed'] for r in runs)==7 and len(selected)==4
 readback=read('build/bbs-lab/zmodem-logon-readback.json');assert readback['level']==50 and readback['exemptions']==0
 assert (ROOT/'build/bbs-lab/zmodem-logon-readback.json').stat().st_mtime_ns >= (ROOT/'build/bbs-lab/results/synchronet/zmodem-window-download-d791-sync-1-logon.json').stat().st_mtime_ns
 retain('build/bbs-lab/zmodem-logon-readback.json')
 setup={}
 for part in ('zmodem','zmodem-selected'):
  path='build/bbs-lab/enigma/'+part+'/setup.json';d=read(path);assert d['passed'] and sha(d['backup'])==d['before_sha256'];setup[part]=d;retain(path);retain(d['backup'])
 provenance=read('build/bbs-lab/synchronet/provenance.json')
 provenance.pop('account',None)
 assert provenance['source_commit']=='9de2c48d0265b07e1a8406d8a55d31df4fad7ee8'
 for name,info in provenance['artifacts'].items():assert sha('build/bbs-lab/synchronet/'+name)==info['sha256']
 retain('build/bbs-lab/synchronet/provenance.json')
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'build/bbs-lab/enigma/source',text=True).strip()==setup['zmodem']['server_commit']
 assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT/'build/bbs-lab/enigma/source',text=True).strip()
 assert sha('build/bbs-lab/enigma/source/docker/bin/sexyz-amd64')==setup['zmodem']['stock_helper_sha256']
 assert sha('build/bbs-lab/enigma/helpers/sexyz')==setup['zmodem']['adapted_helper_sha256']
 assert sha('build/bbs-lab/enigma/source/config/config.hjson')==setup['zmodem-selected']['after_sha256']
 helper_manifest=read('build/bbs-lab/enigma/source/docker/sexyz/manifest.json')
 auditor=read('build/bbs-lab/zmodem-audit/checks.json');assert auditor['passed'] and auditor['checks']==88;source_check(auditor);retain('build/bbs-lab/zmodem-audit/checks.json')
 for key,name in [('wire','zmodem-wire'),('session','zmodem-session'),('dos','zmodem-dos')]:
  (ROOT/'docs/validation'/f'{name}.json').write_text(json.dumps(components[key],indent=2)+'\n')
 sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'lab/bbs').glob('*zmodem*.py')}
 for name in ('lab/bbs/test_transfer_dos.py','lab/bbs/test_ymodem_dos.py','lab/bbs/modem.py','lab/bbs/audit_ymodem.py','lab/bbs/enigma.py','lab/bbs/enigma_transfer.py','lab/bbs/synchronet.py','lab/bbs/synchronet_logon_fixture.py','standalone/test_terminal.py','standalone/terminal_config_fixtures.py','standalone/modem_fixtures.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/test_terminal_ymodem_dos.py','standalone/test_terminal_transfer_dos.py','standalone/record_windowed_zmodem.py','standalone/test_terminal_zmodem_dos.py','standalone/check_zmodem_window.py','standalone/zmodem_window_vectors.py','standalone/check_zmodem_progress_live.py','standalone/check_terminal_zmodem_live.py','standalone/check_terminal_ymodem_live.py','standalone/check_terminal_transfer_live.py','standalone/check_terminal_upload_live.py','standalone/check_zmodem_owners_live.py','standalone/test_zmodem_dos.py','standalone/build_terminal.py','standalone/terminal_memory.py','standalone/prove_source_build.py','Makefile','nix/flake.nix','nix/flake.lock'):
  sources[name]=sha(name)
 storage={}
 for path in ('build/upload-file/checks.json','build/upload-file/manifest.json','build/batch-upload/checks.json','build/batch-download/result.json'):
  d=read(path);source_check(d)
  if 'passed' in d:assert d['passed']
  storage[path]=d;retain(path)
 window=read('build/zmodem-window/checks.json');assert window['passed'] and window['inputs']==79;source_check(window);retain('build/zmodem-window')
 progress=read('build/terminal/zmodem-progress-live-checks.json');assert progress['passed'] and progress['binary_sha256']==RUNTIME and progress['test_sha256']==sha('standalone/check_zmodem_progress_live.py');retain('build/terminal/zmodem-progress-live-checks.json')
 assert progress['case']['replay_ACK_ticks'][-1]-progress['case']['replay_start']==800
 assert all(c['result']['workspace']==9312 and c['result']['ops']==40 for c in components['dos']['cases'])
 historical={}
 for label in ('window-large-f6db','window-large-0ee0'):
  path='build/terminal-zmodem-dos/'+label;historical[label]=read(path+'/checks.json');retain(path)
 assert not historical['window-large-f6db']['passed'] and historical['window-large-0ee0']['passed']
 for checkpoint in ('window-f6db','window-0ee0'):retain('build/checkpoints/'+checkpoint)
 for log in ('window-progress-before2.log','window-progress-after.log'):retain('build/terminal/'+log)
 counterexamples={}
 for key,path in [('retry','build/checkpoints/window-f6db/long-prefix-retry-counterexample.json'),('watchdog','build/checkpoints/window-0ee0/paced-watchdog-counterexample.json')]:
  d=read(path);assert d['expected_failure'] and not d['product_passed'];counterexamples[key]=d;retain(path)
 assert counterexamples['retry']['status']==4 and counterexamples['watchdog']['case']['fault']==3
 assert counterexamples['watchdog']['test_sha256']==sha('standalone/check_zmodem_progress_live.py')
 assert counterexamples['retry']['test_sha256']==sha('standalone/check_zmodem_window.py')
 old_regression=read('build/checkpoints/window-0ee0/setup-profile-regression.json');assert old_regression['complete'] and old_regression['passed'] and len(old_regression['commands'])==78
 for path in ('build/terminal/recheck-window-watchdog-before.py','build/terminal/recheck-window-retry-before.py','build/terminal/window-progress-counterexample.log','build/terminal/window-retry-counterexample.log'):retain(path)
 native=[]
 for address,identity in [('0x1e99a','ev_b40ea3704cb45a1ce2e03f1fc0397c1e23609e7c063273478d8970d3306a310c'),('0x1e69c','ev_b1e782339e069f5f1aab480798650b16c383a7610620aa19bf7be5725d59d951')]:
  path='analysis/pcplus-overlay-anchored-29/functions/'+address+'-c.json';e=json.loads(read(path)['content'][0]['text']);assert e['evidence_id']==identity
  assert e['subject']['digest']['sha256']==sha('analysis/pcplus-overlay-entry-images/overlay-29.analysis.exe')
  native.append(dict(evidence_id=identity,operation=e['operation'],address=address,provider=e['provider'],target_sha256=e['subject']['digest']['sha256'],retained_record_sha256=sha(path)))
 result=dict(passed=True,binary_sha256=RUNTIME,memory_layout=m,baseline_commit='b03ca3154de33fe8ea99407be4ed4642a2018ad7',workspace=dict(engine_bytes=9312,live_context_bytes=8,policy_bytes=10240),components=components,storage=storage,linked=linked,terminal_regression=regression,source_rebuild=dict(output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256'],reports={p:sha(p) for p in ('docs/validation/application-components-source-build.json','docs/validation/terminal-source-build.json')}),actual_DOS=dos,window_peer=window,paced_progress=progress,native_review=native,historical_actual_DOS=historical,counterexamples=counterexamples,prior_broad_regression=old_regression,all_current_checkpoint_workflows_passed=True,required_BBS_runs=selected,all_recorded_runs_passed=False,failed_BBS_attempts=1,failed_historical_DOS_cases=2,BBS_runs=runs,server_provenance=dict(synchronet=provenance,enigma_helper=helper_manifest),enigma_fixture=setup,quota_readback=readback,passive_auditor=auditor,runtime_sources=manifest['sources'],sources=sources,retained_artifacts={str(p):sha(p) for p in sorted(artifacts)},scope='Bounded 8 KiB sender window, 1 KiB payloads, 8 KiB receive. Four current logged-in local BBS workflows and four actual DOS sessions. Eight window/BBS attempts retained. Separate modeled paced replay proves accepted-progress refresh below historical high-water. ENiGMA selector-first fixture bypasses unresolved fragmented-arrow interaction. No physical modem, full loss/timing matrix or whole-application completion claim.')
 (ROOT/'docs/validation/windowed-zmodem.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded windowed sender',RUNTIME,len(artifacts),'retained artifacts; four current BBS workflows')
if __name__=='__main__':main()
