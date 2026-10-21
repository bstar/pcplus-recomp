#!/usr/bin/env python3
"""Owned stock same-call XMODEM cancel/retry reference and unique fixtures."""
import argparse,binascii,hashlib,json,subprocess
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,snapshot,message_bodies,statistics,sha
from synchronet_transfer import BinaryPeer,AREA
from synchronet import ENV

NAME='SXRCN003.BIN';RETRY='SXRUP003.BIN';REFNAME='SXQRF005.BIN';REFRETRY='SXQRF006.BIN'
DESCRIPTION='Synthetic PCPlus audio cancel';RETRY_DESCRIPTION='Synthetic PCPlus audio retry'

def payload(name=NAME):
 assert name in (NAME,REFNAME)
 return hashlib.sha256(name.encode()).digest()+bytes(((i*73+(i>>8)*19)&255)^0x5a for i in range(11521-32))

def stored_files():return {p.name:sha(p) for p in sorted(AREA.iterdir()) if p.is_file()}

def metadata(out,name,label):
 assert name in (NAME,RETRY,REFNAME,REFRETRY) and label in ('before','after')
 prefix='metadata-'+name[:-4]+'-'+label;path=out/(prefix+'.js');assert not path.exists()
 path.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('"+name+"')));f.close();\n")
 r=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(path)],env=ENV(),capture_output=True,text=True,check=True)
 (out/(prefix+'.stdout')).write_text(r.stdout);(out/(prefix+'.stderr')).write_text(r.stderr)
 value=json.loads(r.stdout.split('PCPLAB_JSON:',1)[1].splitlines()[0]);(out/(prefix+'.json')).write_text(json.dumps(value,indent=2)+'\n');return value

def reference(out):
 out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 before=snapshot();bodies=message_bodies();stats=statistics();files=stored_files();data=payload(REFNAME)
 (out/'source.bin').write_bytes(data)
 for name in (REFNAME,REFRETRY):assert name not in files and metadata(out,name,'before') is None
 checks={};error=None;frames=[]
 with BinaryPeer() as peer:
  def phase(label,data=b'',needle=None):
   peer.text.clear();peer.scan_from=0
   if data:peer.send(data,label)
   if needle:peer.wait(needle,30)
   peer.pump(.4);(out/(label+'.bin')).write_bytes(peer.text);(out/(label+'.txt')).write_text(peer.clean)
   return peer.clean
  def start(prefix,name,description):
   phase(prefix+'upload',b'U','Filename:');phase(prefix+'upload-name',name.encode()+b'\r','[Yes] No')
   phase(prefix+'upload-confirm',b'y','Enter a description now.');phase(prefix+'description',description.encode()+b'\r','Protocol, Batch')
   phase(prefix+'protocol',b'1','Hang up after transfer?')
   peer.binary=True;peer.text.clear();peer.octets(b'n');peer.wait('Start XMODEM-1K/CRC transfer now (Ctrl-X to abort):',30)
   banner=b'transfer now (Ctrl-X to abort):';at=peer.text.find(banner);assert at>=0;del peer.text[:at+len(banner)]
   noise=bytearray()
   while True:
    c=peer.take(1)[0]
    if c==67:break
    noise.append(c);assert len(noise)<8192
  def sendframe(number,offset,size):
   body=data[offset:offset+size].ljust(size,b'\x1a');wire=bytes([2 if size==1024 else 1,number,255-number])+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
   peer.octets(wire);assert peer.take(1)==b'\x06'
  def finish(prefix):
   peer.binary=False;peer.wait('[Hit a key]',30);peer.pump(.4)
   (out/(prefix+'completion.bin')).write_bytes(peer.text);(out/(prefix+'completion.txt')).write_text(peer.clean)
   phase(prefix+'post-transfer',b' ','■ File ■')
  try:
   phase('login',needle='Login:');phase('password',b'LABUSER\r','Password:');phase('welcome',b'LABPASS42\r','[Hit a key]')
   phase('bulletins',b' ','Enter number of bulletin or [Quit]');phase('scan',b'Q','Search all groups for new messages?')
   phase('pause',b'n\r','[Hit a key]');phase('main',b' ','Read/Post Messages')
   phase('files',b'T','List Files in dir');phase('join',b'J','Which, Quit');phase('area',b'11\r','■ File ■')
   start('',REFNAME,DESCRIPTION);sendframe(1,0,1024);peer.octets(b'\x18\x18');finish('cancel-')
   assert (AREA/REFNAME).read_bytes()==data[:1024];partial_hash=sha(AREA/REFNAME)
   start('retry-',REFRETRY,RETRY_DESCRIPTION)
   offset=0;number=1
   while offset<len(data):
    size=1024 if len(data)-offset>=1024 else 128;sendframe(number,offset,size)
    frames.append(dict(number=number,bytes=size));offset+=size;number+=1
   peer.octets(b'\x04');assert peer.take(1)==b'\x15';peer.octets(b'\x04');assert peer.take(1)==b'\x06'
   finish('retry-');phase('final',b'Q','Read/Post Messages')
   cm=metadata(out,REFNAME,'after');rm=metadata(out,REFRETRY,'after')
   checks.update(CRC_ACK_then_CAN=True,full_same_call_CRC_retry=True,exact_retry_payload_and_padding=(AREA/REFRETRY).read_bytes()==data+b'\x1a'*127,
    original_partial_preserved=sha(AREA/REFNAME)==partial_hash,official_metadata=cm['size']==1024 and rm['size']==11648,same_connection_return_to_main=True)
  except Exception as exc:error=repr(exc);checks['full_same_call_CRC_retry']=False
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'transcript.txt').write_text(peer.cleaned(peer.history))
 after=statistics();checks.update(server_inputs_preserved=before==snapshot(),message_bodies_preserved=bodies==message_bodies(),
  existing_files_preserved=all(stored_files().get(n)==h for n,h in files.items()),only_expected_new_files=set(stored_files())==set(files)|{REFNAME,REFRETRY},
  no_message_mail_download_writes=all(stats['Total'][k]==after['Total'][k] for k in ('posts','email','feedback','dnloads','dnloadb')))
 result=dict(passed=all(checks.values()),checks=checks,error=error,server=before,frames=frames,statistics_before=stats,statistics_after=after,source_sha256=hashlib.sha256(data).hexdigest(),existing_files=files,
  reference_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/synchronet_transfer.py']},
  scope='One owned stock TCP connection: CRC block/ACK/CAN cancellation, Files, full14-block same-source retry under a fresh remote name, EOT NAK/ACK and Files/Main. Original partial and all prior files preserved. Reference fixed CPR; not DOS/audio/physical or server partial cleanup acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checks','error')}));assert result['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);reference(p.parse_args().output)
