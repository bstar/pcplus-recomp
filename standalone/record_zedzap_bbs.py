#!/usr/bin/env python3
"""Bind the 8 KiB DOS/BBS checkpoint; preserve historical ledgers and failures."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
RUNTIME='d0274a228c0149b4c760e70fcf6dc786bcaf11e469539993e89e80dca74270a3'
def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def source_check(report):
 for path,digest in report.get('sources',{}).items():assert sha(path)==digest,path

def main():
 manifest=read('build/terminal/manifest.json');m=manifest['memory_layout']
 assert manifest['binary_sha256']==sha('build/terminal/TERMINAL.EXE')==RUNTIME
 source_check(manifest)
 assert (m['near_bytes'],m['resident_code_bytes'],m['retained_parent_paragraphs'])==(65088,63038,20323)
 baseline=json.loads(subprocess.check_output(['git','show','c51b0d9:docs/validation/terminal-source-build.json'],cwd=ROOT))['manifest']
 assert [m[k]-baseline['memory_layout'][k] for k in ('near_bytes','resident_code_bytes','retained_parent_paragraphs')]==[32,92,7]
 artifacts=set()
 def retain(path):
  path=Path(path)
  if path.is_dir():artifacts.update(p.relative_to(ROOT) for p in (ROOT/path).rglob('*') if p.is_file() and p.name!='.lock')
  else:assert (ROOT/path).is_file(),path;artifacts.add(path)
 components={}
 for name in ('wire','session','dos'):
  path=f'build/zmodem-{name}/checks.json';d=read(path);assert d['passed'];source_check(d);components[name]=d;retain(path)
 assert components['wire']['host_checks']==5051 and components['wire']['DOS_streams']==79
 assert components['session']['scripted_checks']==92 and len(components['session']['independent_peers'])==22
 assert components['dos']['DOS_cases']==53 and components['dos']['isolated_source_build_byte_identical']
 for peer in components['session']['independent_peers']:
  assert peer['passed'] and sha(peer['command'][0])==peer['peer_sha256']
  for path,digest in peer['retained_wire_sha256'].items():assert sha(path)==digest;retain(path)
 linked={}
 for name,path in [('workflows','terminal-zmodem-live-checks.json'),('owners','zmodem-owners-live-checks.json'),('frames','config-far-checks.json')]:
  file='build/terminal/'+path;d=read(file);assert d['passed'] and d['binary_sha256']==RUNTIME
  if 'test_sha256' in d:assert d['test_sha256']==sha('standalone/'+('check_terminal_zmodem_live.py' if name=='workflows' else 'check_zmodem_owners_live.py'))
  linked[name]=d;retain(file)
 assert linked['workflows']['inputs']==71 and linked['owners']['inputs']==10 and len(linked['frames']['rejected_mutations'])==325
 regression=read('build/terminal/setup-profile-regression.json')
 commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert len(commands)==78 and regression['complete'] and regression['passed'] and regression['binary_sha256']==RUNTIME
 assert [r['command'] for r in regression['commands']]==commands and all(r['exit_code']==0 for r in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==64 and read('docs/validation/terminal-source-build.json')['manifest']==manifest
 for path,d in proof['outputs'].items():assert d['matches_workspace'] and sha('build/'+path)==d['sha256'],path
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==RUNTIME
 for path in ('build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/terminal/manifest.json','build/terminal/setup-profile-regression.json','build/application-source-proof/snapshot.json','build/application-source-proof/result.json','build/application-source-proof/build.log'):retain(path)
 dos=read('build/terminal-zmodem-dos/zedzap-large-d027/checks.json');assert dos['passed'] and dos['binary_sha256']==RUNTIME
 for case in dos['cases']:
  where=Path('build/terminal-zmodem-dos/zedzap-large-d027')/case['case']
  assert case['passed'] and all(case['checks'].values()) and read(where/'result.json')==case
  assert (ROOT/where/'BEFORE.BIN').read_bytes()==(ROOT/where/'AFTER.BIN').read_bytes()
  expected={name:(ROOT/where/'PEER'/name).read_bytes() for name in case['files']}
  for name,data in expected.items():assert (ROOT/where/'RECV'/name).read_bytes()==data and hashlib.sha256(data).hexdigest()==case['files'][name]
  audit=audit_batch((ROOT/where/'peer.bin').read_bytes(),expected)
  assert max(p['length'] for f in audit['files'] for p in f['packets'])==8192
  for f in audit['files']:f.pop('source')
  assert read(where/'protocol-source-audit.json')==audit
 retain('build/terminal-zmodem-dos/zedzap-large-d027')
 required={('synchronet','download'):'zmodem-download-d027-sync-1',('synchronet','upload'):'zmodem-upload-d027-sync-1',('enigma','download'):'zmodem-download-d027-enigma-3',('enigma','upload'):'zmodem-upload-d027-enigma-1'}
 failed_stages={
 'zmodem-download-8c48-sync-1':'Synthetic daily-logon quota rejected login.',
 'zmodem-download-8c48-enigma-1':'Fragmented-arrow selector entered YMODEM; helper exit255.',
 'zmodem-download-8c48-enigma-2':'Historical auditor rejected valid post-EOF recovery; exact file/helper exit/menu passed.',
 'zmodem-download-d027-enigma-1':'Login animation consumed file-menu command; no ZMODEM transfer.',
 'zmodem-download-d027-enigma-2':'Space left a leading blank in command text; no ZMODEM transfer.'}
 runs=[];selected=[]
 for path in sorted((ROOT/'build/bbs-lab/results').glob('*/zmodem-*/result.json')):
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
 assert len(runs)==10 and sum(r['passed'] for r in runs)==5 and len(selected)==4
 readback=read('build/bbs-lab/zmodem-logon-readback.json');assert readback['level']==50 and readback['exemptions']==0;retain('build/bbs-lab/zmodem-logon-readback.json')
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
 auditor=read('build/bbs-lab/zmodem-audit/checks.json');assert auditor['passed'] and auditor['checks']==84;source_check(auditor);retain('build/bbs-lab/zmodem-audit/checks.json')
 for key,name in [('wire','zmodem-wire'),('session','zmodem-session'),('dos','zmodem-dos')]:
  (ROOT/'docs/validation'/f'{name}.json').write_text(json.dumps(components[key],indent=2)+'\n')
 sources={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'lab/bbs').glob('*zmodem*.py')}
 for name in ('standalone/record_zedzap_bbs.py','standalone/test_terminal_zmodem_dos.py','standalone/check_terminal_zmodem_live.py','standalone/check_terminal_ymodem_live.py','standalone/check_terminal_transfer_live.py','standalone/check_terminal_upload_live.py','standalone/check_zmodem_owners_live.py','standalone/test_zmodem_dos.py','standalone/build_terminal.py','standalone/terminal_memory.py','standalone/prove_source_build.py','Makefile','nix/flake.nix','nix/flake.lock'):
  sources[name]=sha(name)
 storage={}
 for path in ('build/upload-file/checks.json','build/upload-file/manifest.json','build/batch-upload/checks.json','build/batch-download/result.json'):
  d=read(path);source_check(d)
  if 'passed' in d:assert d['passed']
  storage[path]=d;retain(path)
 result=dict(passed=True,binary_sha256=RUNTIME,memory_layout=m,baseline_commit='c51b0d9a61c93c22bf78306818c632832bc9390b',workspace=dict(engine_bytes=9308,live_context_bytes=8,policy_bytes=10240),components=components,storage=storage,linked=linked,terminal_regression=regression,source_rebuild=dict(output_count=64,source_snapshot_sha256=proof['source_snapshot_sha256']),actual_DOS=dos,required_BBS_runs=selected,all_recorded_runs_passed=False,failed_attempts=5,BBS_runs=runs,server_provenance=dict(synchronet=provenance,enigma_helper=helper_manifest),enigma_fixture=setup,quota_readback=readback,passive_auditor=auditor,runtime_sources=manifest['sources'],sources=sources,retained_artifacts={str(p):sha(p) for p in sorted(artifacts)},scope='8 KiB receive, 1 KiB send. Four current logged-in local BBS workflows and two actual DOS 8 KiB receive sessions. All ten BBS attempts retained. ENiGMA selector-first fixture bypasses unresolved fragmented-arrow interaction. No physical modem, full loss/timing matrix or whole-application completion claim.')
 (ROOT/'docs/validation/zedzap-bbs.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded',RUNTIME,len(artifacts),'retained artifacts; four current BBS workflows')
if __name__=='__main__':main()
