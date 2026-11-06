#!/usr/bin/env python3
"""Record external failure recovery and a separate core Enigma regression."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','failures','enigma','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert m['experimental_external_viewer'] and digest==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def read(path):
  r=json.loads(path.read_text());assert r['passed'] and r['binary_sha256']==digest,path
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  for n,h in r.get('sources',{}).items():
   if isinstance(h,str):assert sha(ROOT/n)==h,n
  return r
 failures=read(a.failures);names={c['case'] for c in failures['cases']}
 assert names=={'missing-target','missing-comspec','large-comspec','nonzero-child','empty-path-fallback'}
 for c in failures['cases']:assert c['passed'] and all(c['checks'].values())
 e=read(a.enigma/'proxy-integration.json');base=read(a.enigma/'result.json');audit=read(a.enigma/'screen-reference-audit.json')
 assert audit['different_cells']==0 and audit['matched_cells']==1920
 assert not e.get('file_viewer') and base['cpu']=='8086'
 result=dict(passed=True,binary_sha256=digest,application_unchanged=True,physical_deployment_changed=False,
  failures=dict(report=bind(a.failures),cases=failures['cases'],sources=failures['sources']),
  enigma_core=dict(report=bind(a.enigma/'proxy-integration.json'),screen_audit=bind(a.enigma/'screen-reference-audit.json'),matched_cells=audit['matched_cells'],different_cells=0,delivered_bytes=audit['delivered_bytes'],external_viewer_opened=False),
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_external_recovery.py','standalone/build_path_session.py']},
  limits=['DOSBox8086 synthetic serial peer and an isolated SynthModem Telnet proxy against owned stock Enigma; no physical/SIP/audio acceptance.','Missing command and exit37 are processed by COMMAND.COM; these tests do not claim its exit result is propagated as the direct viewer exit status.','DOSBox resolves its built-in COMMAND.COM even with an empty search path; that case establishes successful fallback, not missing-interpreter refusal.',
   'The interpreter-allocation fixture requests65535 extra paragraphs; the passive observer proves a local failure acknowledgement and exact restoration, not a captured DOS error number.','An earlier two-byte malformed MZ was not a valid loader-refusal fixture and timed out; it is excluded.','A first empty-PATH attempt hid the test ADDKEY utility and never dialed; final tests qualify that utility explicitly.','The Enigma regression does not open the external viewer inside the editor. External-child BBS pressure, transfer/reconnect composition, missing/malformed-interpreter rejection on a real DOS kernel and Synchronet on this candidate remain open.','Installed release and private configuration are unchanged.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five external recovery cases and separate exact Enigma core screen')
if __name__=='__main__':main()
