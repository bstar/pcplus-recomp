#!/usr/bin/env python3
"""Exercise passive audit against independent fixtures and malformed captures."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import h,meta,offer,payload
from check_zmodem_wire import packet
from audit_zmodem import audit_batch,audit_controls
def main():
 cases=[]
 def good(name,wire,expected):
  d=audit_batch(wire,expected);assert {f['name']:f['source'] for f in d['files']}==expected
  cases.append(dict(case=name,passed=True))
 def bad(name,wire,expected):
  try:audit_batch(wire,expected)
  except (AssertionError,ValueError):cases.append(dict(case=name,passed=True));return
  raise AssertionError('Accepted '+name)
 for fmt in (65,66,67):
  for n in (0,1,1024,2048,4096,8192):
   data=bytes(i&255 for i in range(n));wire=offer('TEST.BIN',n,fmt)
   if data:wire+=payload(data,0,fmt)
   wire+=h(11,n,fmt)+h(8)+b'OO';good(f'CRC-{fmt}-length-{n}',wire,{'TEST.BIN':data})
   bad(f'missing-OO-{fmt}-{n}',wire[:-2],{'TEST.BIN':data})
   bad(f'bad-size-{fmt}-{n}',wire,{'TEST.BIN':data+b'X'})
   if data:
    corrupt=bytearray(packet(data,fmt,107,0));corrupt[0]^=1
    bad(f'bad-data-CRC-{fmt}-{n}',offer('TEST.BIN',n,fmt)+h(10,0,fmt)+corrupt+h(11,n,fmt)+h(8)+b'OO',{'TEST.BIN':data})
 for ending in (104,105,106,107):
  wire=offer('TEST.BIN',6)+h(10,0,67)+packet(b'ABC',67,ending,0)
  wire+=(h(10,3,67) if ending in (104,107) else b'')+packet(b'DEF',67,107,0)+h(11,6)+h(8)+b'OO'
  good(f'ending-{ending}',wire,{'TEST.BIN':b'ABCDEF'})
 good('duplicate-offer-and-retransmitted-prefix',offer('TEST.BIN',6)+payload(b'ABC')+offer('TEST.BIN',6)+payload(b'ABCDEF')+h(11,6)+h(8)+b'OO',{'TEST.BIN':b'ABCDEF'})
 good('EOF-followed-by-position-recovery',offer('TEST.BIN',6)+payload(b'ABCDEF')+h(11,6)+payload(b'ABCDEF')+h(11,6)+h(8)+b'OO',{'TEST.BIN':b'ABCDEF'})
 for name,wire in [('gap',payload(b'ABC',3)),('wrong-offset-EOF',payload(b'ABC')+h(11,2)),('wrong-bytes',payload(b'BAD'))]:
  bad(name,offer('TEST.BIN',3)+wire+h(8)+b'OO',{'TEST.BIN':b'ABC'})
 wire=offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8)+b'OO';a=audit_batch(wire,{'TEST.BIN':b'ABC'})
 trace=[dict(direction='bbs',seconds=1+2*i,offset=e['offset'],size=e['end']-e['offset']) for i,e in enumerate(a['events'])]
 trace.append(dict(direction='bbs',seconds=13,offset=a['end']-2,size=2))
 def controls(items):
  raw=b'';t=list(trace)
  for kind,pos,when in items:
   data=h(kind,pos);t.append(dict(direction='dos',seconds=when,offset=len(raw),size=len(data)));raw+=data
  return audit_controls(a,raw,t,'bbs',14)
 standard=[(9,0,4),(3,3,8),(1,0x23000000,10),(8,0,12)]
 assert controls(standard);cases.append(dict(case='opposite-headers-timed-positive',passed=True))
 for name,items in [('missing-ACK',[x for x in standard if x[0]!=3]),('wrong-ACK',[(9,0,4),(3,4,8),(1,0x23000000,10),(8,0,12)]),('late-ACK',[(9,0,4),(3,3,15),(1,0x23000000,10),(8,0,12)]),('early-RINIT',[(9,0,4),(3,3,8),(1,0x23000000,6),(8,0,12)]),('wrong-initial-ZRPOS',[(9,1,4),(3,3,8),(1,0x23000000,10),(8,0,12)])]:
  try:controls(items)
  except AssertionError:cases.append(dict(case=name,passed=True));continue
  raise AssertionError('Accepted bad opposite controls: '+name)
 # Retained actual DOS lrzsz captures are optional corroboration, not test inputs.
 out=ROOT/'build/bbs-lab/zmodem-audit';out.mkdir(parents=True,exist_ok=True)
 report=dict(passed=True,checks=len(cases),cases=cases,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_zmodem.py',ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py']},scope='Independent passive audit fixture/negative checks. No real BBS session or C codec execution.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Passed',len(cases),'passive ZMODEM audit checks')
if __name__=='__main__':main()
