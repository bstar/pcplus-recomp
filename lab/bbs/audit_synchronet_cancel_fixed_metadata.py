#!/usr/bin/env python3
"""Record stock receiver retirement/partial accounting after native Escape."""
import argparse,binascii,hashlib,json,re
from pathlib import Path
from audio_synchronet import ROOT,snapshot,sha
from audio_synchronet_cancel_fixed import NAME,AREA,payload,metadata,stored_files

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'cancel-metadata-audit.json').exists()
 r=json.loads((out/'result.json').read_text());assert r['route']=='xmodem-cancel' and snapshot()==r['server']
 value=metadata(out,NAME,'after');target=AREA/NAME;data=target.read_bytes() if target.exists() else b'';expected=payload(NAME)
 log=(out/'server-session.log').read_bytes();source=ROOT/r['upload']['source_path'];stat=source.stat();files=stored_files();before=r['upload']['existing_files_before']
 rows=re.findall(rb'\b([RE])\s+(\d+)\s+\d+ bps\s+\d+ cps\s+(\d+) errors[^\r\n]*SXCAN002\.BIN',log)
 metadata_valid=value is None and not target.exists()
 if value is not None:
  metadata_valid=value['name']==NAME and value['from']=='LABUSER' and value['size']==len(data) and value['sha1']==hashlib.sha1(data).hexdigest() and value['md5']==hashlib.md5(data).hexdigest() and value['crc16']==binascii.crc_hqx(data,0) and value['crc32']==binascii.crc32(data)&0xffffffff
 checks=dict(official_partial_metadata_matches_actual_bytes=metadata_valid,retained_bytes_exact_incomplete_source_prefix=expected.startswith(data) and len(data)<len(expected),
  receiver_retired_with_error_not_full_success=len(rows)==1 and rows[0][0]==b'E' and int(rows[0][1])==len(data),
  DOS_source_identity_preserved=source.read_bytes()==expected and sha(source)==r['upload']['source_sha256'] and [stat.st_ino,stat.st_size,stat.st_mtime_ns]==r['upload']['source_stat'],
  existing_files_preserved=all(files.get(n)==h for n,h in before.items()),no_unexpected_new_file=set(files)-set(before)<={NAME},server_inputs_preserved=snapshot()==r['server'])
 with (out/'receiver-partial.bin').open('xb') as f:f.write(data)
 result=dict(passed=all(checks.values()),checks=checks,metadata=value,receiver_records=[{'status':a.decode(),'bytes':int(b),'reported_errors':int(c)} for a,b,c in rows],
  server_partial_cleanup_accepted=value is None and not target.exists(),server_published_partial_upload=bool(re.search(rb'U\+ uploaded SXCAN002\.BIN',log)) and value is not None,
  partial_bytes=len(data),partial_sha256=hashlib.sha256(data).hexdigest(),
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_cancel_fixed.py',ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py']},
  captures_sha256={n:sha(out/n) for n in ('receiver-partial.bin','metadata-after.js','metadata-after.json','metadata-after.stdout','metadata-after.stderr','result.json','server-session.log')},
  scope='Read-only actual stock receiver retirement and exact partial/official metadata accounting. Expected cancellation E is distinguished from full-file success. Source identity and existing files preserve. A retained/indexed partial keeps server cleanup unaccepted even when client cancellation/menu/teardown passes. No deletion, replacement or invented success.')
 (out/'cancel-metadata-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
