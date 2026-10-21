#!/usr/bin/env python3
"""Pinned stock Synchronet XMODEM-CRC reference and fixture identity."""
import argparse,binascii,json,time
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,statistics,sha
from synchronet_transfer import BinaryPeer,AREA,PAYLOAD

def source():
 p=AREA/'PCXTEST.BIN';assert p.read_bytes()==PAYLOAD
 return p

def reference(out):
 out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 server=snapshot();bodies=message_bodies();before=statistics();path=source();identity=sha(path);checks={};frames=[];error=None
 with BinaryPeer() as peer:
  def phase(label,data=b'',needle=None):
   peer.text.clear();peer.scan_from=0
   if data:peer.send(data,label)
   if needle:peer.wait(needle,30)
   peer.pump(.4)
   (out/(label+'.bin')).write_bytes(peer.text);(out/(label+'.txt')).write_text(peer.clean)
   return peer.clean
  try:
   phase('login',needle='Login:');phase('password',b'LABUSER\r','Password:');phase('welcome',b'LABPASS42\r','[Hit a key]')
   phase('bulletins',b' ','Enter number of bulletin or [Quit]');phase('scan',b'Q','Search all groups for new messages?')
   phase('pause',b'n\r','[Hit a key]');phase('main',b' ','Read/Post Messages')
   phase('files',b'T','List Files in dir');phase('join',b'J','Which, Quit')
   text=phase('area',b'11\r','■ File ■');assert 'PCPlus Lab' in text
   phase('download',b'D','Filespec');phase('filename',b'PCXTEST.BIN\r','Protocol, Batch')
   phase('protocol',b'1','Hang up after transfer?')
   peer.binary=True;peer.text.clear();peer.octets(b'n');peer.pump(.5);peer.text.clear();peer.octets(b'C')
   data=bytearray();expected=1;noise=bytearray()
   while True:
    leader=peer.take(1)[0]
    if leader==4:peer.octets(b'\x06');break
    if leader not in (1,2):noise.append(leader);assert len(noise)<8192;continue
    size=128 if leader==1 else 1024;frame=peer.take(size+4)
    number,comp=frame[:2];body=frame[2:-2];assert number==expected%256 and comp==255-number
    assert int.from_bytes(frame[-2:],'big')==binascii.crc_hqx(body,0)
    data.extend(body);frames.append(dict(sequence=number,bytes=size));expected+=1;peer.octets(b'\x06')
   (out/'received.bin').write_bytes(data)
   assert data==PAYLOAD+b'\x1a'*(len(data)-len(PAYLOAD)) and len(data)==11648
   peer.binary=False;peer.wait('[Hit a key]',30);peer.pump(.4)
   (out/'completion.bin').write_bytes(peer.text);(out/'completion.txt').write_text(peer.clean)
   phase('post-transfer',b' ','■ File ■');phase('final',b'Q','Read/Post Messages')
   checks.update(complete_CRC_frames=True,exact_source_and_SUB_padding=True,post_transfer_file_and_main=True)
  except Exception as exc:error=repr(exc);checks['complete_CRC_frames']=False
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'transcript.txt').write_text(peer.cleaned(peer.history));(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 after=statistics();checks.update(server_inputs_preserved=snapshot()==server,message_bodies_preserved=message_bodies()==bodies,source_unchanged=sha(path)==identity,
  no_message_mail_or_upload_writes=all(before['Total'][k]==after['Total'][k] for k in ('posts','email','feedback','uploads','uploadb')))
 result=dict(passed=all(checks.values()),checks=checks,error=error,frames=frames,server=server,statistics_before=before,statistics_after=after,
  source_path=str(path.relative_to(ROOT)),source_sha256=identity,reference_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/synchronet_transfer.py']},
  scope='Owned stock Synchronet/sexyz XMODEM-1K/CRC TCP reference. Exact11521 source bytes and127SUB padding, real return to File and Main. Reference supplies fixed CPR; not DOS/audio or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checks','error','frames')}));assert result['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);reference(p.parse_args().output)
