#!/usr/bin/env python3
"""Check declared Hayes-fixture hangup guards without filtering ordinary data."""
import argparse
import hashlib
import json
from pathlib import Path
from modem import GuardedHangup

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
cases=[]
for left in range(4):
 for right in range(5):
  f=GuardedHangup(.5,0);wire=bytearray();hits=0
  for data,now in [(b'prior',.1),(b'+++'[:left],1),(b'+++'[left:],1.02),(b'ATH\r'[:right],1.7),(b'ATH\r'[right:],1.72)]:
   forwarded,matched=f.feed(data,now);wire.extend(forwarded);hits+=int(matched)
  assert wire==b'prior' and hits==1 and not f.pending
  cases.append(dict(case='legal-partition-'+str(left)+'-'+str(right),passed=True))
for before,after in ((.4,.7),(.7,.4),(.4,.4)):
 f=GuardedHangup(.5,0);wire=bytearray();hits=0
 for data,now in [(b'prior',.1),(b'+++',.1+before),(b'ATH\r',.1+before+after)]:
  forwarded,matched=f.feed(data,now);wire.extend(forwarded);hits+=int(matched)
 assert wire==b'prior+++ATH\r' and not hits
 cases.append(dict(case='missing-quiet-guard-'+str(before)+'-'+str(after),passed=True))
for partial in (b'+',b'++',b'+++',b'+++A',b'+++AT'):
 f=GuardedHangup(.5,0)
 if len(partial)<=3:f.feed(partial,1)
 else:f.feed(b'+++',1);f.feed(partial[3:],1.6)
 assert f.expire(4)==partial and not f.pending and f.expire(5)==b''
 cases.append(dict(case='bounded-partial-flush-'+partial.hex(),passed=True))
payload=bytes(range(256))+b'+++ATH\r\xff\xff'
for split in range(len(payload)+1):
 f=GuardedHangup(.5,0);f.feed(b'x',.1);wire=bytearray();hits=0
 for data,now in [(payload[:split],.2),(payload[split:],.21)]:
  forwarded,matched=f.feed(data,now);wire.extend(forwarded);hits+=int(matched)
 wire.extend(f.expire(4))
 assert wire==payload and not hits
 cases.append(dict(case='binary-stream-partition-'+str(split),passed=True))
result=dict(passed=True,cases=cases,sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()for path in [Path(__file__).resolve(),ROOT/'lab/bbs/modem.py']},scope=__doc__+' Pure fixture state-machine checks; not Boca S12 settings or a complete Hayes interpreter.')
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS guarded fixture hangup:',len(cases),'cases')
