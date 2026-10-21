#!/usr/bin/env python3
"""Measure packet-boundary and peer-retirement delay from actual cancellation."""
import argparse,json,tarfile
from pathlib import Path
from audio_synchronet import ROOT,LAB,sha
from synchronet import ARTIFACTS
from audit_audio_download import frontend_trace
from test_transfer_dos import timestamp
from modem import Telnet

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'cancel-boundary-diagnosis.json').exists()
 base=json.loads((out/'independent-audit.json').read_text());assert base['passed']
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes']);protocol=base['protocol']
 pause=display.rfind(b'[Hit a key]');assert pause>=0
 pause_time=timestamp(trace,'bbs',pause);assert pause_time>protocol['cancel_seconds']
 assert sha(LAB/'sbbs_src.tgz')==ARTIFACTS['sbbs_src.tgz'];authority={}
 with tarfile.open(LAB/'sbbs_src.tgz') as archive:
  for leaf in ('sexyz.c','xmodem.c'):
   suffix='src/sbbs3/'+leaf;members=[m for m in archive.getmembers() if m.name.endswith(suffix)];assert len(members)==1
   data=archive.extractfile(members[0]).read();path=LAB/'source'/suffix;assert path.read_bytes()==data;authority[str(path.relative_to(ROOT))]=sha(path)
 result=dict(passed=True,cancel_splits_next_frame=protocol['incomplete_next_frame_bytes']>0,
  incomplete_next_frame_bytes=protocol['incomplete_next_frame_bytes'],complete_frames_before_CAN=len(protocol['frames']),
  first_ACK_to_CAN_seconds=protocol['cancel_seconds']-protocol['first_ACK_seconds'],CAN_to_remote_pause_seconds=pause_time-protocol['cancel_seconds'],CAN_to_next_user_input_seconds=protocol['post_input_seconds']-protocol['cancel_seconds'],
  source_authority=authority,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/test_transfer_dos.py',ROOT/'lab/bbs/modem.py']},
  captures_sha256={n:sha(out/n) for n in ('independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl')},
  scope='Passive actual audio cancellation boundary and latency measurement on one frontend monotonic timeline. Pinned stock xmodem_get_block reads a complete payload before CRC and recognizes CAN only at a control boundary. A partial next frame before CAN can therefore delay peer retirement; report measured latency without converting eventual menu recovery into timely cancellation or server cleanup acceptance.')
 (out/'cancel-boundary-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
