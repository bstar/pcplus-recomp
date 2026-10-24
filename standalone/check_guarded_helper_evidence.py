#!/usr/bin/env python3
"""Reject damaged raw evidence without changing any captured file on disk."""
import argparse,contextlib,io,json,struct,sys,traceback
from pathlib import Path
from unittest.mock import patch
import record_guarded_helper as verifier
from prove_guarded_helper_source import sha
ROOT=verifier.ROOT
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 receipt=ROOT/'docs/validation/guarded-helper.json';accepted=json.loads(receipt.read_text());assert accepted['passed']
 for name,digest in accepted['sources'].items():assert sha(ROOT/name)==digest,name
 root=ROOT/'build/guarded-helper'
 trials=[
  ('closed-trap-phase',ROOT/'build/terminal-trap-tests/guarded-helper-traps-02/00/TRAPWIT.BIN',6),
  ('startup-caller-break',ROOT/'build/terminal-trap-tests/guarded-helper-traps-02/00/CHILTRAP.BIN',20),
  ('cancellation-rescue',ROOT/'build/terminal-cancel-tests/guarded-helper-cancel-02/capture/CANCEL.BIN',8),
  ('returned-frame',root/'final-apply-1-00/B1.BIN',0),
  ('register-owner',root/'final-apply-1-00/S1.BIN',0),
  ('helper-child-phase',root/'final-ownership-1-00/S0.BIN',sum(size for _,size in verifier.FIELDS)),
  ('compiled-bytecode',ROOT/'build/connection-dos/heap-final-compiler-1-explicit/LOGON.ASX',0),
  ('BBS-observer',ROOT/'build/bbs-lab/results/synchronet/guarded-helper-sync-02/SCRIPT.BIN',6),
 ]
 original=Path.read_bytes;results=[];argv=sys.argv[:]
 try:
  for name,target,offset in trials:
   target=target.resolve();seen=[];before=sha(target)
   def damaged(path):
    raw=original(path)
    if path.resolve()==target:
     seen.append(True);raw=bytearray(raw);raw[offset]^=1;return bytes(raw)
    return raw
   sys.argv=['record_guarded_helper.py','--root',str(root),'--trap-label','guarded-helper-traps-02',
    '--cancel-label','guarded-helper-cancel-02','--sync-label','guarded-helper-sync-02',
    '--enigma-label','guarded-helper-enigma30-01','--output',str(root/('rejected-'+name+'.json'))]
   assert not(root/('rejected-'+name+'.json')).exists()
   try:
    with patch.object(Path,'read_bytes',damaged),contextlib.redirect_stdout(io.StringIO()):verifier.main()
   except AssertionError as error:
    assert seen,name
    site=traceback.extract_tb(error.__traceback__)[-1]
    results.append(dict(case=name,target=str(target.relative_to(ROOT)),offset=offset,rejected=True,
     target_sha256=before,rejection_file=Path(site.filename).name,rejection_line=site.lineno))
   else:raise AssertionError('Damaged evidence was accepted: '+name)
   assert sha(target)==before and not(root/('rejected-'+name+'.json')).exists()
 finally:sys.argv=argv
 result=dict(passed=True,scope=__doc__,receipt_sha256=sha(receipt),
  checker_sha256=sha(Path(__file__)),verifier_sha256=sha(ROOT/'standalone/record_guarded_helper.py'),cases=results)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS guarded helper evidence:',len(results),'damaged raw inputs rejected; captures unchanged')
if __name__=='__main__':main()
