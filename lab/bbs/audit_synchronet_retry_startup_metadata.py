#!/usr/bin/env python3
"""Official same-call partial custody and full retry storage/metadata audit."""
import argparse,binascii,hashlib,json,re,tarfile
from pathlib import Path
from audio_synchronet import ROOT,LAB,snapshot,sha
from audio_synchronet_retry_startup import NAME,RETRY,AREA,payload,metadata,stored_files
from synchronet import ARTIFACTS,Peer
from modem import Telnet

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'retry-metadata-audit.json').exists()
 r=json.loads((out/'result.json').read_text());assert r['route']=='xmodem-cancel-retry' and snapshot()==r['server']
 observed=json.loads((out/'partial-observer.json').read_text());assert observed['passed'] and observed['retry_metadata_at_observation'] is None
 for n,h in observed['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in observed['captures_sha256'].items():assert sha(out/n)==h,n
 cm=metadata(out,NAME,'after');rm=metadata(out,RETRY,'after');partial=(AREA/NAME).read_bytes();full=(AREA/RETRY).read_bytes();source=payload();st=(AREA/NAME).stat()
 files=stored_files();before=r['upload']['existing_files_before'];local=ROOT/r['upload']['source_path'];local_stat=local.stat()
 def valid(meta,name,data,desc):
  return meta['name']==name and meta['from']=='LABUSER' and desc in meta['desc'] and meta['size']==len(data) and meta['sha1']==hashlib.sha1(data).hexdigest() and meta['md5']==hashlib.md5(data).hexdigest() and meta['crc16']==binascii.crc_hqx(data,0) and meta['crc32']==binascii.crc32(data)&0xffffffff
 log=(out/'server-session.log').read_bytes();rows=re.findall(rb'\b([RE])\s+(\d+)\s+\d+ bps\s+\d+ cps\s+(\d+) errors[^\r\n]*(SXRCN003|SXRUP003)\.BIN',log)
 display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());clean=Peer.cleaned(display);banner='Start XMODEM-1K/CRC transfer now (Ctrl-X to abort):';parts=clean.split(banner);assert len(parts)==3
 controls=[part.split('Processing uploaded file',1)[0].strip() for part in parts[1:]]
 requests=[]
 for i,c in enumerate(controls):
  match=re.fullmatch('C+(\x06){'+str(len(partial)//1024 if i==0 else 14)+'}'+('' if i==0 else '\x15\x06'),c);assert match,repr(c)
  requests.append(len(c)-len(c.lstrip('C')))
 assert len(rows)==2 and rows[0][0]==b'E' and rows[0][3]==b'SXRCN003' and rows[1][0]==b'R' and rows[1][3]==b'SXRUP003'
 assert [int(x[2]) for x in rows]==[n-1 for n in requests]
 assert sha(LAB/'sbbs_src.tgz')==ARTIFACTS['sbbs_src.tgz'];authority={}
 with tarfile.open(LAB/'sbbs_src.tgz') as archive:
  for name in ('sexyz.c','xmodem.c'):
   suffix='src/sbbs3/'+name;members=[m for m in archive.getmembers() if m.name.endswith(suffix)];assert len(members)==1
   path=LAB/'source'/suffix;assert path.read_bytes()==archive.extractfile(members[0]).read();authority[str(path.relative_to(ROOT))]=sha(path)
 checks=dict(partial_bytes_inode_size_mtime_preserved=sha(AREA/NAME)==observed['partial_sha256'] and [st.st_ino,st.st_size,st.st_mtime_ns]==observed['partial_stat'] and partial==(out/'partial-observer/partial.bin').read_bytes(),
  partial_metadata_preserved=cm==observed['partial_metadata'],partial_exact_incomplete_source=source.startswith(partial) and 0<len(partial)<len(source),
  retry_exact_full_same_source_and_padding=full==source+b'\x1a'*127,
  both_official_records_hash_owner_description_correct=valid(cm,NAME,partial,'Synthetic PCPlus audio cancel') and valid(rm,RETRY,full,'Synthetic PCPlus audio retry'),
  receiver_error_then_full_success=int(rows[0][1])==len(partial) and int(rows[1][1])==11648,
  all_reported_errors_are_startup_timeouts=True,
  official_full_upload_log=len(re.findall(rb'U\+ uploaded SXRUP003\.BIN \(11648 bytes\) to Main PCPlus Lab',log))==1,
  DOS_source_identity_preserved=local.read_bytes()==source and sha(local)==r['upload']['source_sha256'] and [local_stat.st_ino,local_stat.st_size,local_stat.st_mtime_ns]==r['upload']['source_stat'],
  existing_files_preserved=all(files.get(n)==h for n,h in before.items()),only_expected_new_files=set(files)==set(before)|{NAME,RETRY},server_inputs_preserved=snapshot()==r['server'])
 for name,data in [('receiver-partial.bin',partial),('receiver-retry.bin',full)]:
  with (out/name).open('xb') as f:f.write(data)
 names=['result.json','server-session.log','bbs-output.bin','partial-observer.json','receiver-partial.bin','receiver-retry.bin']
 names += [p.name for p in out.glob('metadata-*-after.*')]
 result=dict(passed=all(checks.values()),checks=checks,partial_metadata=cm,retry_metadata=rm,startup_requests=requests,startup_timeouts=[n-1 for n in requests],data_block_errors=0,
  receiver_records=[dict(status=a.decode(),bytes=int(b),errors=int(c),name=d.decode()+'.BIN') for a,b,c,d in rows],source_authority=authority,server_partial_cleanup_accepted=False,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_retry_startup.py',ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py',ROOT/'lab/bbs/modem.py']},captures_sha256={n:sha(out/n) for n in names},
  scope='Official E-partial then R-full retry on one call. Exact shared source/padding and both metadata records; partial bytes/inode/size/mtime/metadata match the live pre-completion observer. Startup retries are counted from exact C/ACK controls and pinned official source; no data errors or remote partial cleanup are accepted. Existing files and local source identity preserve.')
 (out/'retry-metadata-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
