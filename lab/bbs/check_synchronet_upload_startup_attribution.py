#!/usr/bin/env python3
"""Reject inconsistent startup-error claims against a completed audio upload.

Mutants are separate ignored cohorts. Refresh their relevant capture hashes so
rejection must come from attribution policy, rather than stale hash metadata.
The accepted cohort, server files and official metadata are never modified.
"""
import argparse,json,re,subprocess,sys
from pathlib import Path
from audio_synchronet import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();source=a.cohort.resolve();out=a.output.resolve()
 assert source.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 assert not out.exists()
 read=lambda n:json.loads((source/n).read_text())
 accepted=read('upload-metadata-audit-v2.json')
 assert accepted['passed'] and all(accepted['checks'].values())
 assert accepted['startup_timeouts']>=1
 for n,h in accepted['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in accepted['captures_sha256'].items():assert sha(source/n)==h,n
 baseline={n:sha(source/n) for n in accepted['captures_sha256']}
 baseline['upload-metadata-audit-v2.json']=sha(source/'upload-metadata-audit-v2.json')
 original=read('upload-metadata-audit.json');base=read('independent-audit.json')
 log=(source/'server-session.log').read_bytes();display=(source/'bbs-output.bin').read_bytes()
 count=accepted['startup_timeouts'];name=accepted['metadata']['name'].encode()
 pattern=rb'(?m)^(\s*)R(\s+11648\s+\d+ bps\s+\d+ cps\s+)'+str(count).encode()+rb'( errors[^\r\n]*'+re.escape(name)+rb'[^\r\n]*)(\r?)$'
 assert len(re.findall(pattern,log))==1
 def counter(value,status=b'R'):
  return re.sub(pattern,lambda m:m[1]+status+m[2]+str(value).encode()+m[3]+m[4],log)
 controls=b'C'*accepted['startup_requests']+b'\x06'*14+b'\x15\x06'
 assert display.count(controls)==1
 cases=[
  ('extra_DSZ_error','server-session.log',counter(count+1),'assert matches=='),
  ('missing_DSZ_error','server-session.log',counter(count-1),'assert matches=='),
  ('failed_receive_status','server-session.log',counter(count,b'E'),'assert matches=='),
  ('missing_startup_request','bbs-output.bin',display.replace(controls,controls[1:],1),'assert matches=='),
  ('data_NAK','bbs-output.bin',display.replace(controls,controls.replace(b'\x06',b'\x15',1),1),'assert re.fullmatch'),
  ('replayed_frame',None,None,'assert len(protocol'),
  ('additional_failed_metadata_gate',None,None,"assert not original['passed']"),
 ]
 out.mkdir();results=[];auditor=ROOT/'lab/bbs/audit_synchronet_upload_metadata_v2.py'
 for label,leaf,value,guard in cases:
  target=out/label;target.mkdir()
  for item in source.iterdir():
   if item.name!='upload-metadata-audit-v2.json':(target/item.name).symlink_to(item)
  current=json.loads(json.dumps(original))
  if leaf:
   (target/leaf).unlink();(target/leaf).write_bytes(value)
   if leaf in current['captures_sha256']:current['captures_sha256'][leaf]=sha(target/leaf)
  if label=='replayed_frame':
   changed=json.loads(json.dumps(base));changed['protocol']['frames'].append(dict(changed['protocol']['frames'][-1]))
   (target/'independent-audit.json').unlink();(target/'independent-audit.json').write_text(json.dumps(changed)+'\n')
  if label=='additional_failed_metadata_gate':
   assert current['checks']['official_name_owner_description_and_size']
   current['checks']['official_name_owner_description_and_size']=False
  (target/'upload-metadata-audit.json').unlink();(target/'upload-metadata-audit.json').write_text(json.dumps(current)+'\n')
  result=subprocess.run([sys.executable,str(auditor),str(target)],capture_output=True,text=True)
  (target/'negative.stdout').write_text(result.stdout);(target/'negative.stderr').write_text(result.stderr)
  checks=dict(nonzero_exit=result.returncode!=0,expected_policy_guard=guard in result.stderr,
              assertion_rejection='AssertionError' in result.stderr,no_acceptance_written=not (target/'upload-metadata-audit-v2.json').exists())
  results.append(dict(name=label,passed=all(checks.values()),checks=checks,returncode=result.returncode,
                      stderr_sha256=sha(target/'negative.stderr')))
 unchanged=all(sha(source/n)==h for n,h in baseline.items())
 result=dict(passed=unchanged and all(c['passed'] for c in results),cases=results,original_captures_unchanged=unchanged,
             baseline_sha256=baseline,source_cohort=str(source.relative_to(ROOT)),
             inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),auditor)},
             scope='Seven attribution-policy counterexamples on separate rehashed copies of actual upload evidence. Not new DOS/audio or physical hardware runs. The original failed zero-error audit and accepted captures remain exact.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'cases':[(c['name'],c['passed']) for c in results],'original_captures_unchanged':unchanged}))
 assert result['passed']


if __name__=='__main__':main()
