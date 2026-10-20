#!/usr/bin/env python3
"""Stage and test normal SynthModem VM startup with the rebuilt helper."""
import argparse,gzip,json,os,re,shutil,signal,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,REV,MEDIA,sha,records,archive

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
 p.add_argument('--profile',choices=['auto','v32bis'],default='auto')
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 source=a.source.resolve();candidate=a.candidate.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==REV
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=source,text=True).strip()
 ledger=ROOT/'docs/validation/synthmodem-pressure.json';pins=json.loads(ledger.read_text())['candidate_sha256']
 assert all(sha(candidate/n)==h for n,h in pins.items())
 names=['lab/bbs/synthmodem_runtime.py','lab/bbs/synthmodem_runtime.js','lab/bbs/synthmodem_vm_control.py',
  'nix/flake.nix','nix/flake.lock','tools/modem-dev','lab/bbs/patches/synthmodem-control/control.patch',str(ledger.relative_to(ROOT))]
 frozen={n:sha(ROOT/n) for n in names}
 stage=out/'source';stage.mkdir()
 for n in ('src','vm/qemu-runner'):shutil.copytree(source/n,stage/n)
 shutil.copyfile(source/'config.js',stage/'config.js')
 for n in pins:
  (stage/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate/n,stage/n)
 staged={str(p.relative_to(stage)):sha(p) for p in stage.rglob('*') if p.is_file()}
 built=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes',
  'build',str(ROOT/'nix')+'#synthmodem-control-i386','--no-link','--json'],text=True))
 helper=Path(built[0]['outputs']['out'])/'bin/modemd-ctrl';elf=helper.read_bytes()
 assert elf[:5]==b'\x7fELF\x01' and struct.unpack_from('<H',elf,18)[0]==3
 assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(helper)],text=True)
 media={n:source/'vm/images'/n for n in MEDIA};assert all(sha(media[n])==h for n,h in MEDIA.items())
 shutil.copyfile(media['bzImage'],out/'bzImage')
 original=records(gzip.decompress(media['rootfs-slmodemd-pjsip.cpio.gz'].read_bytes()))
 assert sum(n=='usr/local/bin/modemd-ctrl' for n,_,_ in original)==1
 entries=[(n,f,elf if n=='usr/local/bin/modemd-ctrl' else b) for n,f,b in original]+[('TRAILER!!!',[0]*13,b'')]
 image=out/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
 rebuilt=records(gzip.decompress(image.read_bytes()));old={n:d for n,_,d in original};new={n:d for n,_,d in rebuilt}
 assert set(new)==set(old) and [n for n in old if old[n]!=new[n]]==['usr/local/bin/modemd-ctrl']
 with (out/'node.log').open('w') as log:
  run=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_runtime.js'),str(stage),str(out),a.profile],stdout=log,stderr=log,start_new_session=True)
  try:run.wait(timeout=150)
  except BaseException:
   # QEMU belongs to the test process group even if Node cannot finish cleanup.
   os.killpg(run.pid,signal.SIGTERM)
   try:run.wait(timeout=3)
   finally:
    try:os.killpg(run.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   raise
 assert run.returncode==0,f'Runtime test failed; see {out}/node-error.txt and node.log'
 r=json.loads((out/'node-result.json').read_text())
 def packets(name):
  wire=(out/name).read_bytes();at=0;answer=[]
  while at<len(wire):
   assert at+4<=len(wire);size=struct.unpack_from('<I',wire,at)[0];at+=4
   assert size>=12 and at+size<=len(wire);b=wire[at:at+size];at+=size
   assert b[0]==0x80 and b[1]&127==0
   answer.append(b)
  return answer
 tx=packets('rtp-to-modem.bin');rx=packets('rtp-from-modem.bin')
 r['checks']['independent_sent_silence']=len(tx)>=300 and all(b[12:]==bytes([255])*160 and struct.unpack_from('>HI',b,2)==(i,i*160) for i,b in enumerate(tx))
 # Decode G.711 mu-law independently, inspect actual sample energy. This
 # establishes non-silent answering DSP audio, not a particular modulation.
 pcm=[]
 for b in rx:
  for v in b[12:]:
   v^=255;t=(((v&15)<<3)+132)<<((v>>4)&7);pcm.append(132-t if v&128 else t-132)
 r['checks']['independent_received_audio']=len(rx)>=300 and max(map(abs,pcm))>100
 r['audio']={'samples':len(pcm),'peak':max(map(abs,pcm)),'mean_square':sum(v*v for v in pcm)/len(pcm)}
 frames=json.loads((out/'tunnel-frames.json').read_text())
 sip=[bytes.fromhex(f['hex']) for f in frames if f['channel']==0]
 r['checks']['independent_guest_SIP']=any(b.startswith(b'SIP/2.0 200') and b'CSeq:' in b and b'INVITE' in b for b in sip) and any(b.startswith(b'SIP/2.0 200') and b'BYE' in b for b in sip)
 if a.profile=='v32bis':
  guest=(out/'qemu.log').read_text()
  r['checks']['direct_V32bis_entry']=bool(re.search(r'change dp: --> 132\b',guest)) and 'v32: create...' in guest and 'tx_rate=14400,rx_rate=14400' in guest and 'V8_ANS_SEND_ANSAM' not in guest
 r['checks']['frozen_inputs_unchanged']=all(sha(ROOT/n)==h for n,h in frozen.items()) and all(sha(stage/n)==h for n,h in staged.items())
 r.update({'passed':all(r['checks'].values()),'upstream_revision':REV,'frozen_inputs':frozen,'candidate_sha256':pins,
  'staged_source_sha256':staged,'Nix_build':built,'helper_sha256':sha(helper),'media_sha256':MEDIA,
  'candidate_image_sha256':sha(image),'archive_entries_changed':['usr/local/bin/modemd-ctrl'],'archive_entries_added':[],
  'captures_sha256':{n:sha(out/n) for n in ('rtp-to-modem.bin','rtp-from-modem.bin','control-wire.bin','tunnel-frames.json','qemu.log','node.log')},
  'qemu_version':subprocess.check_output(['qemu-system-i386','--version'],text=True).splitlines()[0]})
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'passed':r['passed'],'checks':r['checks'],'commands':r['commands'],'result':str(out/'result.json')},indent=2))
 return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
