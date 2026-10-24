#!/usr/bin/env python3
"""Reject damaged lookup evidence using read overlays; captured files stay intact."""
import argparse,contextlib,io,json,sys,traceback
from pathlib import Path
from unittest.mock import patch
import record_hook_lookup as verifier
from prove_guarded_helper_source import sha
ROOT=verifier.ROOT
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 receipt=ROOT/'docs/validation/hook-lookup.json';accepted=json.loads(receipt.read_text());assert accepted['passed']
 for name,digest in accepted['sources'].items():assert sha(ROOT/name)==digest,name
 root=ROOT/'build/hook-lookup';batch=root/'final-lookup-1-batch-collision'
 policy=root/'final-linked/result.json';policy_bytes=policy.read_bytes()
 forged=policy_bytes.index(b'"original_status": 37')+len(b'"original_status": ')
 quantum=ROOT/'build/aspect-register-parent/ASPECT.EXE'
 trials=[
  ('selected-helper',root/'final-lookup-1-pcplus-file/BIN/APPLYCH.EXE',0),
  ('COM-decoy',batch/'CALL.COM',1),
  ('batch-qualification',batch/'BATARGS.TXT',1),
  ('fixture-mode',root/'final-lookup-1-pcplus-file/MODE.BIN',0),
  ('KEY-target',root/'final-lookup-1-pcplus-file/ACTIONS.KEY',2),
  ('returned-registers',root/'final-lookup-1-pcplus-file/S1.BIN',0),
  ('returned-frame',root/'final-lookup-1-pcplus-file/B1.BIN',0),
  ('native-result-with-pass-flag',policy,forged),
  ('register-owner',ROOT/'build/connection-dos/register-lookup-final-register-1-normal/OWNER0.BIN',0),
  ('compiled-output',ROOT/'build/connection-dos/heap-hook-lookup-final-compiler-1-explicit/LOGON.ASX',0),
  ('interpreter-image',quantum,0),
  ('observer-address',ROOT/'build/bbs-lab/results/synchronet/lookup-final-sync/SCRIPT.BIN',6),
 ]
 original_bytes=Path.read_bytes;original_text=Path.read_text;argv=sys.argv[:];results=[]
 try:
  for name,target,offset in trials:
   target=target.resolve();before=sha(target);seen=[];output=root/('rejected-'+name+'.json');assert not output.exists()
   def changed(path):
    raw=bytearray(original_bytes(path));raw[offset]^=1;seen.append(True);return bytes(raw)
   def read_bytes(path):return changed(path)if path.resolve()==target else original_bytes(path)
   def read_text(path,*args,**kwargs):
    if path.resolve()==target:return changed(path).decode(kwargs.get('encoding')or'utf-8',kwargs.get('errors')or'strict')
    return original_text(path,*args,**kwargs)
   sys.argv=['record_hook_lookup.py','--root',str(root),'--trap-label','lookup-final-traps','--cancel-label','lookup-final-cancel',
    '--sync-label','lookup-final-sync','--enigma-label','lookup-final-enigma30','--register-prefix','lookup-final-register','--output',str(output)]
   try:
    with patch.object(Path,'read_bytes',read_bytes),patch.object(Path,'read_text',read_text),contextlib.redirect_stdout(io.StringIO()):verifier.main()
   except AssertionError as error:
    assert seen,name;site=traceback.extract_tb(error.__traceback__)[-1]
    results.append(dict(case=name,target=str(target.relative_to(ROOT)),offset=offset,rejected=True,target_sha256=before,
     rejection_file=Path(site.filename).name,rejection_line=site.lineno))
   else:raise AssertionError('Damaged evidence accepted: '+name)
   assert sha(target)==before and not output.exists()
 finally:sys.argv=argv
 result=dict(passed=True,cases=results,scope=__doc__,receipt_sha256=sha(receipt),checker_sha256=sha(Path(__file__)),
  verifier_sha256=sha(ROOT/'standalone/record_hook_lookup.py'),shared_verifier_sha256=sha(ROOT/'standalone/record_guarded_helper.py'))
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS lookup evidence:',len(results),'damaged inputs rejected; captures unchanged')
if __name__=='__main__':main()
