#!/usr/bin/env python3
"""Read official FileBase metadata after the owned audio download has exited."""
import argparse,binascii,hashlib,json,re,subprocess
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,sha,snapshot
from audio_synchronet_download import source
from synchronet import ENV,Peer
from modem import Telnet

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('cohort',type=Path);out=parser.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'download-metadata-audit.json').exists()
 run=json.loads((out/'result.json').read_text());assert run['route']=='xmodem-download' and snapshot()==run['server']
 script=out/'download-metadata.js'
 script.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('PCXTEST.BIN')));f.close();\n")
 result=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(script)],env=ENV(),capture_output=True,text=True,check=True)
 (out/'download-metadata.stdout').write_text(result.stdout);(out/'download-metadata.stderr').write_text(result.stderr)
 metadata=json.loads(result.stdout.split('PCPLAB_JSON:',1)[1].splitlines()[0]);data=source().read_bytes()
 display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());clean=Peer.cleaned(display)
 counts=re.findall(r'Times D/Led\s*:\s*(\d+)',clean);assert len(counts)==1,counts
 checks=dict(official_name_and_size=metadata['name']=='PCXTEST.BIN' and metadata['size']==len(data)==11521,
  official_payload_hashes=metadata['crc16']==binascii.crc_hqx(data,0) and metadata['crc32']==binascii.crc32(data)&0xffffffff and metadata['sha1']==hashlib.sha1(data).hexdigest() and metadata['md5']==hashlib.md5(data).hexdigest(),
  official_download_count_advanced_once=metadata['times_downloaded']==int(counts[0])+1,
  authoritative_success_log=len(re.findall(rb'D- downloaded PCXTEST\.BIN \(11521 bytes\) from Main PCPlus Lab',(out/'server-session.log').read_bytes()))==1,
  source_still_exact=sha(source())==run['download']['sha256'],server_inputs_preserved=snapshot()==run['server'])
 receipt=dict(passed=all(checks.values()),checks=checks,metadata=metadata,displayed_download_count_before=int(counts[0]),
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/audio_synchronet_download.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/modem.py']},
  captures_sha256={n:sha(out/n) for n in ('download-metadata.js','download-metadata.stdout','download-metadata.stderr','result.json','bbs-output.bin','server-session.log')},
  scope='Read-only official FileBase.get plus exact source/hash, one successful server-log download and one metadata-count advancement from the displayed pre-transfer value. Run after the producer exits; no server/account/config mutation.')
 (out/'download-metadata-audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));assert receipt['passed']
