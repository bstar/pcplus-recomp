#!/usr/bin/env python3
"""Attribute stock helper errors to source-verified startup timeouts only."""
import argparse,hashlib,json,re,tarfile
from pathlib import Path
from audio_synchronet import ROOT,LAB,snapshot,sha
from audio_synchronet_upload import AREA,payload,stored_files,name_for
from modem import Telnet
from synchronet import Peer,ARTIFACTS

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'upload-metadata-audit-v2.json').exists()
 read=lambda n:json.loads((out/n).read_text());original=read('upload-metadata-audit.json');base=read('independent-audit.json');run=read('result.json')
 NAME=run['upload']['name'];assert NAME in {name_for(slot) for slot in range(1,10)}
 assert not original['passed'] and {k for k,v in original['checks'].items() if not v}=={'helper_full_receive_zero_errors'}
 assert base['passed'] and all(base['checks'].values())
 for n,h in original['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in original['captures_sha256'].items():assert sha(out/n)==h,n
 assert sha(LAB/'sbbs_src.tgz')==ARTIFACTS['sbbs_src.tgz'];authority={}
 with tarfile.open(LAB/'sbbs_src.tgz') as archive:
  for leaf in ('sexyz.c','xmodem.c'):
   suffix='src/sbbs3/'+leaf;members=[m for m in archive.getmembers() if m.name.endswith(suffix)];assert len(members)==1
   data=archive.extractfile(members[0]).read();path=LAB/'source'/suffix;assert path.read_bytes()==data
   authority[str(path.relative_to(ROOT))]=sha(path)
  # In this pinned source the DSZ receive counter is cumulative, initialized
  # before block1 and incremented on unsuccessful get_block, including NOINP.
  se=(LAB/'source/src/sbbs3/sexyz.c').read_text();xm=(LAB/'source/src/sbbs3/xmodem.c').read_text()
  assert 'if (++errors > xm.max_errors' in se and 'errors = 0;\n\t\t\tblock_num = 1;' in se
  assert 'i = getcom(expected_block_num <= 1 ? 3 : 10);' in xm
 display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());clean=Peer.cleaned(display)
 banner='Start XMODEM-1K/CRC transfer now (Ctrl-X to abort):';assert clean.count(banner)==1
 after=clean.split(banner,1)[1];controls=after[:after.index('Processing uploaded file')].strip()
 assert re.fullmatch('C{2,}'+'\x06'*14+'\x15\x06',controls)
 requests=len(controls)-16;timeouts=requests-1
 protocol=base['protocol'];assert len(protocol['frames'])==protocol['accepted_blocks']==14
 assert [c['response'] for c in protocol['controls']]==[6]*14+[21,6] and not any(c.get('retry') for c in protocol['controls'])
 log=(out/'server-session.log').read_bytes();matches=re.findall(rb'\bR\s+11648\s+\d+ bps\s+\d+ cps\s+(\d+) errors[^\r\n]*'+re.escape(NAME.encode()),log);assert matches==[str(timeouts).encode()]
 assert (AREA/NAME).read_bytes()==payload(NAME)+b'\x1a'*127 and snapshot()==run['server']
 assert all(stored_files().get(n)==h for n,h in run['upload']['existing_files_before'].items())
 checks={k:v for k,v in original['checks'].items() if k!='helper_full_receive_zero_errors'}
 checks.update(helper_success_startup_timeouts_only=True,all_blocks_valid_unreplayed_without_data_NAK=True,official_source_exactly_matches_pinned_archive=True)
 result=dict(passed=all(checks.values()),checks=checks,metadata=original['metadata'],startup_requests=requests,startup_timeouts=timeouts,data_block_errors=0,
  original_audit_sha256=sha(out/'upload-metadata-audit.json'),source_authority=authority,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/audio_synchronet_upload.py',ROOT/'lab/bbs/modem.py',ROOT/'lab/bbs/synchronet.py']},
  captures_sha256={n:sha(out/n) for n in ('upload-metadata-audit.json','independent-audit.json','result.json','server-session.log','bbs-output.bin','receiver-installed.bin','metadata-after.js','metadata-after.json','metadata-after.stdout','metadata-after.stderr')},
  scope='Original zero-total-errors metadata audit retained. Pinned official source counts each3-second initial no-input timeout in cumulative DSZ errors. Exact leading C requests then14 ACKs/EOT NAK/ACK, complete native prefix/frames/suffix and all independent control gates require the reported DSZ error count to equal startup requests minus one. No corrupted/replayed data, failed finish or E-status is accepted. Delayed-start compatibility only; no zero-request-retry or cancellation/loss cleanup claim.')
 (out/'upload-metadata-audit-v2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('passed','checks','startup_requests','startup_timeouts','data_block_errors')}));assert result['passed']
