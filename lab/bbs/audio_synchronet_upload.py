#!/usr/bin/env python3
"""Pinned stock Synchronet XMODEM-CRC upload reference and unique synthetic payloads."""
import argparse,binascii,hashlib,json,time,subprocess
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,snapshot,message_bodies,statistics,sha
from synchronet_transfer import BinaryPeer,AREA
from synchronet import ENV
NAME="SXAUDIO1.BIN"
REFNAME="SXAUREF2.BIN"
DESCRIPTION="Synthetic PCPlus audio upload"

def payload(name):
 assert name in (NAME,REFNAME)
 return hashlib.sha256(name.encode()).digest()+bytes(((i*73+(i>>8)*19)&255)^0x5a for i in range(11521-32))

def stored_files():
 return {p.name:sha(p) for p in sorted(AREA.iterdir()) if p.is_file()}

def metadata(out,name,label):
 assert name in (NAME,REFNAME) and label in ('before','after')
 path=out/('metadata-'+label+'.js');assert not path.exists()
 path.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('"+name+"')));f.close();\n")
 r=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(path)],env=ENV(),capture_output=True,text=True,check=True)
 (out/('metadata-'+label+'.stdout')).write_text(r.stdout);(out/('metadata-'+label+'.stderr')).write_text(r.stderr)
 value=json.loads(r.stdout.split('PCPLAB_JSON:',1)[1].splitlines()[0]);(out/('metadata-'+label+'.json')).write_text(json.dumps(value,indent=2)+'\n');return value

def reference(out):
 out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 server=snapshot();bodies=message_bodies();before=statistics();name=REFNAME;data=payload(name);(out/'source.bin').write_bytes(data);files=stored_files();assert name not in files and metadata(out,name,'before') is None;checks={};frames=[];error=None;after_meta=None
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
   phase('upload',b'U','Filename:');phase('upload-name',name.encode()+b'\r','[Yes] No')
   phase('upload-confirm',b'y','Enter a description now.');phase('description',DESCRIPTION.encode()+b'\r','Protocol, Batch')
   phase('protocol',b'1','Hang up after transfer?')
   peer.binary=True;peer.text.clear();peer.octets(b'n');noise=bytearray()
   peer.wait('Start XMODEM-1K/CRC transfer now (Ctrl-X to abort):',30)
   banner=b'transfer now (Ctrl-X to abort):';at=peer.text.find(banner);assert at>=0
   del peer.text[:at+len(banner)]
   while True:
    c=peer.take(1)[0]
    if c==67:break
    noise.append(c);assert len(noise)<8192
   offset=0;number=1
   while offset<len(data):
    size=1024 if len(data)-offset>=1024 else 128;body=data[offset:offset+size].ljust(size,b'\x1a')
    frame=bytes([2 if size==1024 else 1,number,255-number])+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
    peer.octets(frame);assert peer.take(1)==b'\x06'
    frames.append(dict(sequence=number,bytes=size));number+=1;offset+=size
   peer.octets(b'\x04');first_eot=peer.take(1);assert first_eot==b'\x15'
   peer.octets(b'\x04');assert peer.take(1)==b'\x06'
   peer.binary=False;peer.wait('[Hit a key]',30);peer.pump(.4)
   (out/'completion.bin').write_bytes(peer.text);(out/'completion.txt').write_text(peer.clean)
   phase('post-transfer',b' ','■ File ■');phase('final',b'Q','Read/Post Messages')
   after_meta=metadata(out,name,'after')
   checks.update(complete_CRC_frames_and_two_EOT_finish=True,exact_source_and_SUB_padding=(AREA/name).read_bytes()==data+b'\x1a'*127,official_metadata=after_meta['name']==name and after_meta['size']==11648,post_transfer_file_and_main=True)
  except Exception as exc:error=repr(exc);checks['complete_CRC_frames_and_two_EOT_finish']=False
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'transcript.txt').write_text(peer.cleaned(peer.history));(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 after=statistics();checks.update(server_inputs_preserved=snapshot()==server,message_bodies_preserved=message_bodies()==bodies,source_unchanged=(out/'source.bin').read_bytes()==data,existing_files_preserved=all(stored_files().get(n)==h for n,h in files.items()),only_new_expected_file=set(stored_files())==set(files)|{name},
  no_message_mail_or_download_writes=all(before['Total'][k]==after['Total'][k] for k in ('posts','email','feedback','dnloads','dnloadb')))
 result=dict(passed=all(checks.values()),checks=checks,error=error,frames=frames,server=server,statistics_before=before,statistics_after=after,
  upload_name=name,source_sha256=hashlib.sha256(data).hexdigest(),metadata_after=after_meta,existing_files=files,reference_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/synchronet_transfer.py']},
  scope='Owned stock Synchronet/sexyz XMODEM-1K/CRC upload TCP reference. Unique11521 source bytes and127SUB padding installed with official metadata; native peer sends real CRC frames and NAK/ACK two-EOT finish, then returns to Files/Main. Reference supplies fixed CPR; not DOS/audio or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checks','error','frames')}));assert result['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);reference(p.parse_args().output)
