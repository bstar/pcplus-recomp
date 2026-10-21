#!/usr/bin/env python3
"""Exercise passive audit against independent fixtures and malformed captures."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import h,meta,offer,payload
from check_zmodem_wire import packet
from audit_zmodem import audit_batch,audit_controls
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
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
 # Asynchronous Q ACK may arrive after later data; future positions may not.
 wire=offer('TEST.BIN',6)+h(10,0,67)+packet(b'ABC',67,106,0)+packet(b'DEF',67,104,0)+h(11,6)+h(8)+b'OO'
 a=audit_batch(wire,{'TEST.BIN':b'ABCDEF'})
 trace=[dict(direction='bbs',seconds=1+2*i,offset=e['offset'],size=e['end']-e['offset']) for i,e in enumerate(a['events'])]
 trace.append(dict(direction='bbs',seconds=15,offset=a['end']-2,size=2))
 for name,items,accepted in [
  ('delayed-Q-ACK',[(9,0,4),(3,3,10),(1,0x23000000,12),(8,0,14)],True),
  ('cumulative-Q-ACK',[(9,0,4),(3,6,10),(1,0x23000000,12),(8,0,14)],True),
  ('future-Q-ACK',[(9,0,4),(3,7,10),(1,0x23000000,12),(8,0,14)],False),
  ('unsent-Q-ACK',[(9,0,4),(3,6,8),(1,0x23000000,12),(8,0,14)],False)]:
  # controls() uses a14-second post deadline; FIN at14 is allowed here.
  try:controls(items)
  except AssertionError:assert not accepted,name
  else:assert accepted,name
  cases.append(dict(case=name,passed=True))
 # Required EOF bytes and its optional trailing flow octet are separate input
 # observations. Replying after LF but before XON is valid; before LF is not.
 for flow in (17,19):
  wire=offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8)+b'OO'
  a=audit_batch(wire,{'TEST.BIN':b'ABC'});eof=next(e for e in a['events'] if e['kind']=='header' and e['type']==11)
  assert eof['response_end']==eof['end']-1 and wire[eof['end']-1]==17
  wire=wire[:eof['end']-1]+bytes([flow])+wire[eof['end']:];a=audit_batch(wire,{'TEST.BIN':b'ABC'})
  trace=[]
  for i,e in enumerate(a['events']):
   if e['kind']=='header' and e['type']==11:
    trace.append(dict(direction='bbs',seconds=1+2*i,offset=e['offset'],size=e['response_end']-e['offset']))
    trace.append(dict(direction='bbs',seconds=10.5,offset=e['response_end'],size=e['end']-e['response_end']))
   else:trace.append(dict(direction='bbs',seconds=1+2*i,offset=e['offset'],size=e['end']-e['offset']))
  trace.append(dict(direction='bbs',seconds=13,offset=a['end']-2,size=2))
  assert controls(standard);cases.append(dict(case='EOF-reply-before-optional-flow-'+str(flow),passed=True))
  premature=[(kind,pos,8.5 if kind==1 else when) for kind,pos,when in standard]
  try:controls(premature)
  except AssertionError:cases.append(dict(case='EOF-reply-before-required-LF-'+str(flow),passed=True))
  else:raise AssertionError('Accepted completion before mandatory EOF header bytes')
 # Older retained protocols lack response_end; keep their conservative bound.
 wire=offer('TEST.BIN',3)+payload(b'ABC')+h(11,3)+h(8)+b'OO';a=audit_batch(wire,{'TEST.BIN':b'ABC'})
 for event in a['events']:event.pop('response_end',None)
 trace=[dict(direction='bbs',seconds=1+2*i,offset=e['offset'],size=e['end']-e['offset']) for i,e in enumerate(a['events'])]
 trace.append(dict(direction='bbs',seconds=13,offset=a['end']-2,size=2))
 assert controls(standard);cases.append(dict(case='legacy-protocol-without-response-end',passed=True))
 trace.append(dict(trace[0]))
 try:controls(standard)
 except AssertionError as error:assert str(error)=='Overlapping observed chunks';cases.append(dict(case='overlapping-timing-rows-reject',passed=True))
 else:raise AssertionError('Accepted ambiguous overlapping trace rows')
 # Retained actual DOS lrzsz captures are optional corroboration, not test inputs.
 out=ROOT/'build/bbs-lab/zmodem-audit';out.mkdir(parents=True,exist_ok=True)
 report=dict(passed=True,checks=len(cases),cases=cases,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_zmodem.py',ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py']},scope='Independent passive audit fixture/negative checks. No real BBS session or C codec execution.')
 target=args.output.resolve() if args.output else out/'checks.json'
 if args.output:assert target.is_relative_to(ROOT/'build') and not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(report,indent=2)+'\n');print('Passed',len(cases),'passive ZMODEM audit checks')
if __name__=='__main__':main()
