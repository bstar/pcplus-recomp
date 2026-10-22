#!/usr/bin/env python3
"""Download the >64KiB fixture from stock ENiGMA with a real lrzsz TCP peer."""
import argparse,json,os,select,shutil,subprocess,time
from pathlib import Path
import enigma,synchronet,enigma_transfer
from modem import Telnet
from audit_zmodem import audit_batch,audit_controls
from prepare_audio_pressure_download import NAME,SIZE,validate,entries
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 executable=shutil.which('rz');assert executable,'Run this reference through ./tools/dev (pinned lrzsz)'
 fixture=a.fixture.resolve();fixture_info=json.loads(fixture.read_text());server_fixture=fixture_info.get('server_fixture')
 if server_fixture:
  from enigma_fixture import from_result
  assert from_result(dict(server_fixture=server_fixture,server_root=server_fixture['source'],route='download'))==server_fixture
 source,before=validate(fixture);out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);recv=out/'RECV';recv.mkdir()
 rz=Path(executable).resolve();log=enigma.SOURCE/'logs/enigma-bbs.log';boundary=(log.stat().st_ino,log.stat().st_size)
 def rows():
  assert log.stat().st_ino==boundary[0]
  with log.open('rb') as f:f.seek(boundary[1]);return [json.loads(line) for line in f if line.strip()]
 def menu():
  names=[r['menuName'] for r in rows() if r.get('menuName')];return names[-1] if names else None
 synchronet.HOST=enigma.HOST;synchronet.PORT=enigma.PORT
 steps=[];error=None;child=None;receiver_wire=bytearray();receiver_input=bytearray();checks={};protocol=None
 with synchronet.Peer() as peer:
  def plain(data):
   peer.text.extend(data);peer.history.extend(data)
   while b'\x1b[6n' in peer.text[peer.scan_from:]:
    at=peer.text.find(b'\x1b[6n',peer.scan_from);peer.scan_from=at+4;peer.send(b'\x1b[1;1R','declared-CPR-home')
  peer.plain=plain
  def step(name,data=b'',delay=.7):
   if data:peer.send(data,name)
   peer.pump(delay);steps.append(dict(name=name,menu=menu()));print(json.dumps(steps[-1]),flush=True)
  try:
   step('matrix',delay=3);step('login',b'\r');step('username',enigma.USERNAME.encode()+b'\r');step('password',enigma.PASSWORD.encode()+b'\r',2)
   for i in range(20):
    current=menu()
    if current=='mainMenu':break
    step(f'advance-{i}',b'\x1b' if current=='fullLoginSequenceOnelinerz' else b'N' if current=='fullLoginSequenceNewScanConfirm' else b'\r',1)
   assert menu()=='mainMenu',menu()
   for name,data in [('files',b'F\r'),('search',b'S\r'),('filename',NAME.encode()+b'\r'),('search-submit',b'\r'),('tag',b'T'),('list-quit',b'Q'),('search-quit',b'\x1b'),('download-manager',b'D\r'),('download-all',b'A')]:step(name,data)
   assert menu()=='fileTransferProtocolSelection',menu()
   with (out/'receiver.stderr').open('xb') as stderr:
    child=subprocess.Popen([str(rz),'-b','-q'],cwd=recv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,bufsize=0)
    def incoming(data):
     peer.text.extend(data);peer.history.extend(data);receiver_input.extend(data)
     if child.poll() is None:
      try:child.stdin.write(data)
      except BrokenPipeError:pass # Exact wire/finish/file gates below remain mandatory.
    peer.plain=incoming;peer.send(b'\r','ZMODEM-select');deadline=time.monotonic()+90
    while child.poll() is None and time.monotonic()<deadline:
     readable,_,_=select.select([child.stdout],[],[],0)
     if readable:
      data=os.read(child.stdout.fileno(),65536)
      if data:receiver_wire.extend(data);peer.send(data.replace(b'\xff',b'\xff\xff'),'real-lrzsz-control')
     peer.pump(.02)
    assert child.poll() is not None,'Reference receiver deadline'
    tail=child.stdout.read()
    if tail:receiver_wire.extend(tail);peer.send(tail.replace(b'\xff',b'\xff\xff'),'real-lrzsz-final-control')
    checks['real_reference_receiver_exit_zero']=child.returncode==0
   peer.plain=plain;step('after-helper',delay=2)
   assert menu()=='fileBaseMainMenu',menu()
   step('post-search',b'S\r');step('post-filename',NAME.encode()+b'\r');step('post-search-submit',b'\r')
   checks['post_transfer_search_and_list']=menu()=='fileBaseListEntries'
   sent,_=Telnet().feed(bytes(peer.tx));display,_=Telnet().feed(bytes(peer.rx));protocol=audit_batch(display,{NAME:source.read_bytes()})
   decoders={d:Telnet() for d in ('in','out')};buffers={d:bytearray() for d in decoders};trace=[]
   for event in peer.events:
    d=event['direction'];body,_=decoders[d].feed(bytes.fromhex(event['hex']));offset=len(buffers[d]);buffers[d].extend(body)
    if body:trace.append(dict(direction='bbs' if d=='in' else 'dos',offset=offset,size=len(body),seconds=event['time']))
   assert bytes(buffers['in'])==display and bytes(buffers['out'])==sent
   post=next(e['time'] for e in peer.events if e.get('label')=='post-search')
   protocol['controls']=audit_controls(protocol,sent,trace,'bbs',post)
   for f in protocol['files']:assert f.pop('source')==source.read_bytes()
   checks['complete_source_CRC_EOF_ZFIN_OO_and_opposite_controls']=True
  except Exception as exc:error=repr(exc)
  finally:
   if child is not None and child.poll() is None:child.kill();child.wait()
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'receiver-input.bin').write_bytes(receiver_input);(out/'receiver-output.bin').write_bytes(receiver_wire)
   (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 after=entries();selected=[e for e in after if e['fileName']==NAME];server_rows=rows()
 (out/'server-session.json').write_text(json.dumps(server_rows,indent=2)+'\n');(out/'metadata-after.json').write_text(json.dumps(after,indent=2)+'\n')
 checks.update(exact_source_and_reference_file=(recv/NAME).is_file() and (recv/NAME).read_bytes()==source.read_bytes() and len(source.read_bytes())==SIZE,
  only_expected_reference_file={p.name for p in recv.iterdir()}=={NAME},
  official_download_count_advanced=len(selected)==1 and selected[0]['meta'].get('dl_count',0)==before[0]['meta'].get('dl_count',0)+1,
  owned_helper_exit_zero=sum(r.get('msg')=='Process exited' and r.get('exitCode')==0 for r in server_rows)==1,
  selected_helper_identity=len([r for r in server_rows if r.get('msg')=='Executing external protocol'])==1 and next((r.get('cmd') for r in server_rows if r.get('msg')=='Executing external protocol'),None)==str(enigma_transfer.HELPER),
  no_error=error is None)
 try:validate(fixture);checks['fixture_and_prior_files_metadata_preserved']=True
 except Exception as exc:checks['fixture_and_prior_files_metadata_preserved']=False;error=error or repr(exc)
 r=dict(passed=all(checks.values()),checks=checks,error=error,fixture=str(fixture.relative_to(ROOT)),fixture_sha256=sha(fixture),steps=steps,
  server_fixture=server_fixture,server_root=str(enigma.SOURCE),server_config_sha256=sha(enigma.SOURCE/'config/config.hjson'),
  receiver_path=str(rz),receiver_sha256=sha(rz),reference_bytes=SIZE,reference_sha256=sha(source),protocol=protocol,
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/prepare_audio_pressure_download.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/enigma.py',ROOT/'lab/bbs/modem.py',ROOT/'lab/bbs/audit_zmodem.py')},
  captures_sha256={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},
  scope='Actual '+('isolated sender-candidate' if server_fixture else 'stock owned')+' ENiGMA loopback TCP download to independent real lrzsz receiver. Exact65797-byte source/CRC/EOF/ZFIN/OO/opposite controls, selected helper identity, official accounting and post-helper Search/List are mandatory. Declared CPR reference, no DOS/audio/sustained slow-link/physical or full-application acceptance. No protocol replies are fabricated by this wrapper.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':checks,'error':error}));assert r['passed']


if __name__=='__main__':main()
