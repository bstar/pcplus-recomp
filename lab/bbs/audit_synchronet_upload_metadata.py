#!/usr/bin/env python3
"""Official post-upload metadata, full source/padding and helper-success audit."""
import argparse,binascii,hashlib,json,re
from pathlib import Path
from audio_synchronet import ROOT,snapshot,sha
from audio_synchronet_upload import AREA,payload,metadata,stored_files,name_for

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'upload-metadata-audit.json').exists()
 run=json.loads((out/'result.json').read_text());assert run['route']=='xmodem-upload' and snapshot()==run['server']
 NAME=run['upload']['name'];assert NAME in {name_for(slot) for slot in range(1,10)}
 value=metadata(out,NAME,'after');data=(AREA/NAME).read_bytes();before=run['upload']['existing_files_before'];files=stored_files();log=(out/'server-session.log').read_bytes()
 source=ROOT/run['upload']['source_path'];stat=source.stat()
 checks=dict(official_name_owner_description_and_size=value['name']==NAME and value['from']=='LABUSER' and 'Synthetic PCPlus audio upload' in value['desc'] and value['size']==len(data)==11648,
  exact_full_source_and_padding=data==payload(NAME)+b'\x1a'*127,
  official_hashes=value['crc16']==binascii.crc_hqx(data,0) and value['crc32']==binascii.crc32(data)&0xffffffff and value['sha1']==hashlib.sha1(data).hexdigest() and value['md5']==hashlib.md5(data).hexdigest(),
  one_authoritative_upload_log=len(re.findall(rb'U\+ uploaded '+re.escape(NAME.encode())+rb' \(11648 bytes\) to Main PCPlus Lab',log))==1,
  helper_full_receive_zero_errors=bool(re.search(rb'\bR\s+11648\s+\d+ bps\s+\d+ cps\s+0 errors[^\r\n]*'+re.escape(NAME.encode()),log)),
  source_identity_preserved=sha(source)==run['upload']['source_sha256'] and [stat.st_ino,stat.st_size,stat.st_mtime_ns]==run['upload']['source_stat'],
  existing_server_files_preserved=all(files.get(n)==h for n,h in before.items()),only_expected_new_file=set(files)==set(before)|{NAME},server_inputs_preserved=snapshot()==run['server'])
 with (out/'receiver-installed.bin').open('xb') as f:f.write(data)
 r=dict(passed=all(checks.values()),checks=checks,metadata=value,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_upload.py',ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py']},
  captures_sha256={n:sha(out/n) for n in ('receiver-installed.bin','metadata-after.js','metadata-after.json','metadata-after.stdout','metadata-after.stderr','result.json','server-session.log')},
  scope='Read-only official FileBase.get validates full11521 source plus127SUB padding, owner/description/hash/size, complete zero-error helper receive and one upload log. Source inode/size/mtime and all existing files preserve. Does not substitute for CRC/control/whole-stream/cleanup acceptance; stock partial uploads can be indexed after errors.')
 (out/'upload-metadata-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
