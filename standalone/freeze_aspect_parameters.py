#!/usr/bin/env python3
"""Freeze authored typed-parameter/string fixtures with explicit expectations.

The optional freezer reads private original compiler results. Source-only builds
consume its JSON output and never need the original executable or installation.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
REPORT='analysis/aspect-parameters/compiler-03/report.json'
REPORT_SHA='e2847417384412e1cc0e7886e3b3010db70aba1706504c056233eeecd101b05f'

# Hand-derived from authored source and by-value typed call/frame contracts.
# These are independent expectations, not results of running the maintained VM
# or inferring arithmetic/string truth from compilation success.
EXPECTED={
 'STRRECUR':{'string0':'LIVE','error':'stack','limit':65000},
 'PARZERO':{'string0':'ALIVE','error':'divide_zero'},
 'PARFHEAP':{'string0':'ALIVE','error':'float'},
 'INTARG':{'integer0':7},
 'LONGARG':{'long0':65537},
 'STRARG':{'string0':'HELLO'},
 'EMPTYSTR':{'string0':''},
 'MIXED':{'integer0':7,'long0':65537,'string0':'HELLO'},
 'COMMAS':{'integer0':7,'long0':65537,'string0':'HELLO'},
 'STRLOCAL':{'string0':'HELLO'},
 'STRGLOB':{'string0':'HELLO','string1':'HELLO'},
 'STRMUT':{'string0':'ORIGINAL','string1':'CHANGED'},
 'INTMUT':{'integer0':7,'integer1':9},
 'LONGMUT':{'long0':65537,'long1':65539},
 'STRGASS':{'string0':'HELLO','string1':'HELLO'},
 'STRLASS':{'string0':'HELLO'},
 'STRINIT':{'string0':'HELLO'},
 'STRMAX':{'string0':'A'*80},
 'STRNEST':{'string0':'HELLO'},
 'INTS2':{'integer0':7,'integer1':9},
 'LONGS2':{'long0':65537,'long1':65539},
 'STRS2':{'string0':'FIRST','string1':'SECOND'},
 'FLOAT':{'error':'float'},
 'INTEVAL':{'integer0':11},
 'LONGEVAL':{'long0':65542},
 'NESTEVAL':{'integer0':12},
 'LOCEVAL':{'integer0':12},
}


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
 path=ROOT/REPORT;raw=path.read_bytes();assert sha(raw)==REPORT_SHA
 report=json.loads(raw);assert report['compiler_sha256']==SHA
 assert report['harness_sha256']==sha((ROOT/'standalone/aspect_parameter_probe.py').read_bytes())
 accepted=[c for c in report['cases'] if c['success']]
 rejected=[c for c in report['cases'] if not c['success']]
 assert len(report['cases'])==40 and len(accepted)==27 and len(rejected)==13
 assert set(c['name'] for c in accepted)==set(EXPECTED)
 vectors=[]
 for case in accepted:
  source=case['source'].encode('ascii');wire=bytes.fromhex(case['hex'])
  assert sha(source)==case['source_sha256'] and sha(wire)==case['asx_sha256']
  assert (path.parent/(case['name']+'.ASP')).read_bytes()==source
  assert (path.parent/(case['name']+'.ASX')).read_bytes()==wire
  vector={k:case[k] for k in ['name','intent','source','source_sha256','hex','asx_sha256']}
  vector['expected']=EXPECTED[case['name']]
  vector['dos_excluded']=False
  vectors.append(vector)
 failures=[]
 for case in rejected:
  assert case['errors'] and sha(case['source'].encode('ascii'))==case['source_sha256']
  failures.append({k:case[k] for k in ['name','source','source_sha256','errors','log_sha256']})
 result=dict(compiler_sha256=SHA,private_report=REPORT,private_report_sha256=REPORT_SHA,
  probe_sha256=report['harness_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),
  vectors=vectors,rejected=failures,
  expectation_model='Explicit source-level bank/string snapshots. Typed call arguments have independent by-value storage; mutations of formal parameters do not change caller globals. Arithmetic is precomputed into a typed local before WITH; expected values11,65542,12,12 are hand-derived. Empty/80-character strings retain exact authored content. Float service is intentionally unavailable.',
  findings=['WITH required; commas optional between typed actual arguments.',
   'Direct arithmetic actual arguments rejected in spaced, unspaced, parenthesized and bracketed forms tested; precomputing into typed local accepted.',
   'CC marks numeric actual pushes; CD string actual pushes; framedC8 call carries32-bit absolute target.',
   'Numeric parameter selectors97/98 carry16-bit frame-relative offsets; string parameter selector96 likewise.',
   'StringassignmentAC uses global8C indexbyte, localA0 offsetword or formal96 offsetword; authored assignment records end with00 mode byte.',
   'Exact runtime/string ownership and parameter behavior must be established by execution tests, not these compiler observations.'],
  prior_canonical_report='analysis/aspect-parameters/compiler-02/report.json',
  prior_accepted_outputs_reproduced=24,
  scope='Original compiler output for authored scripts only, with independent expected outcomes. No original executable/application/resource bytes. Compiler corpus and maintained runtime correctness remain separate claims.')
 target=ROOT/'standalone/fixtures/aspect_parameter_vectors.json';target.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(path=str(target.relative_to(ROOT)),vectors=len(vectors),rejected=len(failures),
  completions=sum('error' not in v['expected'] for v in vectors),float_stops=sum(v['expected'].get('error')=='float' for v in vectors),
  fixture_sha256=sha(target.read_bytes()),freezer_sha256=result['freezer_sha256']),indent=2))


if __name__=='__main__':main()
