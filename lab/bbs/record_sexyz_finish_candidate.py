#!/usr/bin/env python3
"""Bind the isolated Nix receiver candidate to its source and scoped tests."""
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 paths=list(map(Path,(ROOT/'build/bbs-lab/sexyz-finish-build-paths.txt').read_text().splitlines()))
 baseline=next(p for p in paths if 'source-baseline' in p.name)
 candidate=next(p for p in paths if 'finish-candidate' in p.name)
 before=baseline/'share/sexyz-source';after=candidate/'share/sexyz-source'
 manifest=json.loads((before/'source-manifest.json').read_text())
 assert manifest==json.loads((after/'source-manifest.json').read_text())
 assert manifest['source_digest']=='79bbd980581e7b90c4bc4506d948b0554919e40634b0bde84b3e67d76c660455'
 changed=[]
 for name,value in manifest['files'].items():
  assert sha(before/name)==value
  if sha(after/name)!=value:changed.append(name)
 assert changed==['sexyz.c'],changed
 module=ROOT/'lab/bbs/patches/sexyz-receive-finish'
 for name,path in {'receive_finish.c':module/'receive_finish.c','receive_finish.h':module/'receive_finish.h',
  'zmodem_wire.c':ROOT/'src/transfer/zmodem_wire.c','zmodem_wire.h':ROOT/'src/transfer/zmodem_wire.h'}.items():
  assert (after/name).read_bytes()==path.read_bytes(),name
 receipts={'bounds':'build/bbs-lab/sexyz-finish-bounds-03/checks.json',
  'peers':'build/bbs-lab/sexyz-receive-finish-candidate-01/checks.json',
  'integration':'build/bbs-lab/sexyz-finish-integration-02/checks.json'}
 reports={k:json.loads((ROOT/n).read_text()) for k,n in receipts.items()}
 assert reports['bounds']['passed'] and len(reports['bounds']['cases'])==24
 assert reports['integration']['passed'] and len(reports['integration']['cases'])==10
 assert reports['peers']['evidence_consistent'] and reports['peers']['candidate_waits_for_OO']
 assert [v['receiver_exited_while_OO_withheld'] for v in reports['peers']['cases']]==[True,True,False,False]
 assert reports['integration']['candidate_sha256']==sha(candidate/'bin/sexyz')
 for name,value in reports['bounds']['module_sha256'].items():assert sha(ROOT/name)==value
 for name,value in reports['bounds']['upstream_header_sha256'].items():assert sha(after/name)==value
 for key,script in [('bounds','check_sexyz_finish_bounds.py'),('peers','check_sexyz_receive_finish.py'),('integration','check_sexyz_finish_integration.py')]:
  assert reports[key]['checker_sha256']==sha(ROOT/'lab/bbs'/script)
 old=json.loads((ROOT/'docs/validation/synthmodem-audio-upload-02.json').read_text())
 assert sha(ROOT/'build/terminal/TERMINAL.EXE')==old['terminal_sha256']
 server=ROOT/'build/bbs-lab/enigma/source'
 for name,value in old['server_inputs'].items():assert sha(server/name)==value,name
 for name,value in old['runtime_inputs'].items():assert sha(Path(name))==value,name
 stock=next(v for v in reports['peers']['cases'] if v['receiver']=='stock-SEXYZ')
 assert stock['receiver_sha256']==old['producer_inputs']['build/bbs-lab/enigma/helpers/sexyz']
 rebuilt=ROOT/'build/bbs-lab/sexyz-finish-rebuild.stderr.log'
 assert 'checking outputs of' in rebuilt.read_text()
 paths_info=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes','path-info','--json','--json-format','2',str(baseline),str(candidate)],text=True))
 sources=['nix/flake.nix','nix/flake.lock','nix/sexyz-receive-finish.nix','tools/cut-sexyz-source.py',
  'lab/bbs/check_sexyz_finish_bounds.py','lab/bbs/check_sexyz_receive_finish.py','lab/bbs/check_sexyz_finish_integration.py',
  str(Path(__file__).relative_to(ROOT)),str((module/'receive_finish.c').relative_to(ROOT)),str((module/'receive_finish.h').relative_to(ROOT)),
  'src/transfer/zmodem_wire.c','src/transfer/zmodem_wire.h']
 result={'passed':True,'candidate_audio_accepted':False,'stock_audio_upload_accepted':False,
  'upstream_commit':manifest['upstream_commit'],'standalone_source_digest':manifest['source_digest'],
  'original_source_files':len(manifest['files']),'changed_upstream_C_headers':changed,
  'packages':paths_info,'baseline_sha256':sha(baseline/'bin/sexyz'),'candidate_sha256':sha(candidate/'bin/sexyz'),
  'Nix_rebuild_check':{'command':'nix build ./nix#sexyz-receive-finish-candidate --rebuild --no-link',
   'observed_exit_code':0,'stderr_sha256':sha(rebuilt)},
  'checks':reports,'source_sha256':{n:sha(ROOT/n) for n in sources},
  'receipt_sha256':{n:sha(ROOT/n) for n in receipts.values()},
  'stock_server_and_runtime_inputs_unchanged':True,'DOS_binary_unchanged':old['terminal_sha256'],
  'scope':'Pinned Nix source-built baseline/candidate with exact shipped source digest and successful Nix reproducibility check.24 modeled-boundary C-owner cases, four real receiver comparisons and ten real candidate fault cases. Every peer case uses the original11521-byte all-octet workload. Stock early retirement remains reproduced; no acceptance gate waived. Candidate is isolated, not configured in the BBS; DOS binary, stock server/helper and SIP/DSP runtime remain unchanged. No new audio/BBS or physical/F01-F16 acceptance.'}
 target=ROOT/'docs/validation/sexyz-receive-finish-candidate.json';assert not target.exists()
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'candidate_sha256':result['candidate_sha256'],'modeled_cases':24,'real_receiver_comparisons':4,'real_candidate_fault_cases':10,'candidate_audio_accepted':False}))


if __name__=='__main__':main()
