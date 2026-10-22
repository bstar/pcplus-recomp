#!/usr/bin/env python3
"""Real file rotations and loopback relay evidence survive finalizer failure."""
import argparse,json,socket,threading
from pathlib import Path
import enigma
from bbs_log_capture import begin,collect,CaptureError
from synthmodem_bbs_dos import Relay
from synthmodem_vm_control import ROOT,sha


def line(n):return json.dumps(dict(record=n)).encode()+b'\n'


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--retained-cohort',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[]
 def files(label):
  d=out/label;d.mkdir();log=d/'bbs.log';log.write_bytes(line(0));marker=d/'boundary.json';begin(log,marker);return d,log,marker
 for rotations in (0,1,2):
  d,log,marker=files('rotation-'+str(rotations));expected=[]
  with log.open('ab') as f:f.write(line(1));expected.append(dict(record=1))
  for i in range(rotations):
   for old in range(i-1,-1,-1):(d/f'bbs.log.{old}').rename(d/f'bbs.log.{old+1}')
   log.rename(d/'bbs.log.0');log.write_bytes(line(i+2));expected.append(dict(record=i+2))
  got=collect(marker,d/'capture');assert got==expected
  meta=json.loads((d/'capture/result.json').read_text())
  for s in meta['segments']:assert sha(d/'capture'/s['capture'])==s['sha256']
  rows.append(dict(case=f'actual-numeric-rename-{rotations}',passed=True,records=len(got)))
 d=out/'partial-at-boundary';d.mkdir();log=d/'bbs.log';log.write_bytes(line(0)+b'{"record":')
 marker=d/'boundary.json';begin(log,marker)
 with log.open('ab') as f:f.write(b'1}\n')
 assert collect(marker,d/'capture')==[dict(record=1)]
 rows.append(dict(case='partial-initial-record-completes-after-boundary',passed=True))
 for label in ('changed-prefix','truncated-original','missing-original','missing-intermediate','partial-record','invalid-record','duplicate-original'):
  d,log,marker=files(label)
  if label=='changed-prefix':log.write_bytes(line(9))
  elif label=='truncated-original':log.write_bytes(b'')
  elif label=='missing-original':log.unlink();log.write_bytes(line(1))
  elif label=='missing-intermediate':log.rename(d/'bbs.log.1');log.write_bytes(line(2))
  elif label=='partial-record':
   with log.open('ab') as f:f.write(b'{"record":1}')
  elif label=='invalid-record':
   with log.open('ab') as f:f.write(b'bad-json\n')
  else:(d/'bbs.log.0').hardlink_to(log)
  try:collect(marker,d/'capture')
  except CaptureError:rows.append(dict(case='reject-'+label,passed=True))
  else:raise AssertionError(label)
 for durable in (False,True):
  d=out/('relay-durable' if durable else 'relay-default');d.mkdir()
  request=bytes(range(256))*17+b'REQUEST';response=bytes(reversed(range(256)))*19+b'RESPONSE'
  peer=socket.socket();peer.bind(('127.0.0.1',0));peer.listen(1);peer.settimeout(5);errors=[];observed=bytearray()
  def serve():
   try:
    client,_=peer.accept()
    with client:
     client.settimeout(5)
     while len(observed)<len(request):
      block=client.recv(4096);assert block;observed.extend(block)
     client.sendall(response)
   except Exception as exc:errors.append(repr(exc))
   finally:peer.close()
  enigma.PORT=peer.getsockname()[1];server=threading.Thread(target=serve,daemon=True);server.start()
  relay=Relay(capture_dir=d if durable else None);relay.thread.start();received=bytearray()
  with socket.create_connection(('127.0.0.1',relay.port),timeout=5) as client:
   client.sendall(request)
   while len(received)<len(response):
    block=client.recv(4096);assert block;received.extend(block)
  server.join(5);relay.thread.join(5)
  assert not server.is_alive() and not relay.thread.is_alive() and not relay.errors and not errors
  assert observed==relay.to_bbs==request and received==relay.from_bbs==response
  if durable:
   # The original failure occurred after the relay completed, during log
   # finalization. A later exception must not lose the already observed wire.
   try:raise RuntimeError('modeled producer finalization failure')
   except RuntimeError:pass
   assert (d/'bbs-input.bin').read_bytes()==request and (d/'bbs-output.bin').read_bytes()==response
   events=[json.loads(s) for s in (d/'BBS-relay-events.jsonl').read_text().splitlines()];assert events==relay.trace
   for direction,expected in [('to_bbs',request),('from_bbs',response)]:
    end=0
    for event in events:
     if event['direction']==direction:assert event['offset']==end;end+=event['count']
    assert end==len(expected)
  else:assert not list(d.iterdir())
  rows.append(dict(case='real-loopback-relay-'+str(durable),passed=True,request_bytes=len(request),response_bytes=len(response)))
 retained_inputs={}
 if a.retained_cohort:
  cohort=a.retained_cohort.resolve();assert cohort.is_relative_to(ROOT/'build')
  expected_path=cohort/'recovered-server-session.jsonl'
  expected=[json.loads(s) for s in expected_path.read_text().splitlines()]
  sessions={r['sessionId'] for r in expected if r.get('msg')=='User "loclab" successfully logged in'};assert len(sessions)==1
  session=next(iter(sessions));old_path=cohort/'preserved-server-logs/enigma-bbs.log.0';current_path=cohort/'preserved-server-logs/enigma-bbs.log'
  old=old_path.read_bytes();current=current_path.read_bytes();offset=0
  for raw in old.splitlines(keepends=True):
   if json.loads(raw).get('sessionId')==session:break
   offset+=len(raw)
  else:raise AssertionError('Actual retained session absent')
  d=out/'retained-journal-replay';d.mkdir();log=d/'bbs.log';log.write_bytes(old[:offset]);marker=d/'boundary.json';begin(log,marker)
  with log.open('ab') as f:f.write(old[offset:])
  log.rename(d/'bbs.log.0');log.write_bytes(current)
  got=collect(marker,d/'capture');assert [r for r in got if r.get('sessionId')==session]==expected
  retained_inputs={str(p.relative_to(ROOT)):sha(p) for p in (old_path,current_path,expected_path)}
  rows.append(dict(case='retained-real-journal-content-with-synthetic-boundary',passed=True,exact_actual_session_records=len(expected),
   limitation='A synthetic test boundary reproduces the preserved rotated journal content; it does not restore the lost original boundary/relay capture or grant acceptance to the failed producer.'))
 result=dict(passed=True,case_count=len(rows),cases=rows,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/bbs_log_capture.py',ROOT/'lab/bbs/synthmodem_bbs_dos.py']},
  retained_inputs=retained_inputs,captures_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
  scope='Actual temporary file append/rename rotations and rejected damaged histories, plus real bidirectional loopback TCP with unmodified binary/control octets. Capture-enabled/default relays preserve observed streams; a modeled later finalizer exception cannot erase disk evidence. No live BBS/DOS/audio or power-loss acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,case_count=len(rows))))


if __name__=='__main__':main()
