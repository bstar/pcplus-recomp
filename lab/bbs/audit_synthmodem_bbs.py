#!/usr/bin/env python3
"""Read-only wire/serial/server/video audit; keep failed editor semantics failed."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from modem import Telnet
from audit_zmodem import audit_batch,audit_controls
from test_transfer_dos import timestamp

ROOT=Path(__file__).resolve().parents[2]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(out):
 report=json.loads((out/'result.json').read_text())
 for n,h in report['frozen_inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in report['wire_sha256'].items():assert sha(out/n)==h,n
 sent,_=Telnet().feed((out/'to-bbs.bin').read_bytes())
 display,_=Telnet().feed((out/'from-bbs.bin').read_bytes())
 assert sent==(out/'sent.bin').read_bytes() and display==(out/'display.bin').read_bytes()
 raw=(out/'node-serial-in.bin').read_bytes()
 prefix=re.match(rb'ATZ\rATD1\r127\.0\.0\.1:\d+\r',raw)
 assert prefix and raw[prefix.end():]==sent,'Raw serial/Telnet payload mismatch'
 assert display in (out/'node-serial-out.bin').read_bytes(),'Server display altered before serial output'
 before=(out/'BEFORE.BIN').read_bytes()
 assert len(before)==42 and before==(out/'AFTER.BIN').read_bytes()
 rows=[json.loads(x) for x in (out/'server-session.jsonl').read_text().splitlines()]
 assert {r['sessionId'] for r in rows}=={report['session']}
 assert any(r.get('msg')=='User "loclab" successfully logged in' for r in rows)
 assert not any('posted message to' in r.get('msg','') for r in rows)
 menus=[r['menuName'] for r in rows if r.get('menuName')]
 assert menus==report['menus']
 semantic={}
 if report['route']=='menus':
  wanted=iter(['mainMenu','messageBaseMainMenu','mainMenu','fileBaseMainMenu']);current=next(wanted)
  for m in menus:
   if m==current:current=next(wanted,None)
  semantic['ordered_main_messages_main_files']=current is None
  screen=(out/'SCREEN.BIN').read_bytes()[::2].decode('cp437')
  semantic['final_file_menu_visible']='file base >>' in screen.lower() and menus[-1]=='fileBaseMainMenu'
 elif report['route']=='editor':
  clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437')
  positions=[(int(r),int(c)) for r,c in re.findall(r'(?:INS|OVR) (\d+),(\d+)',clean[clean.find('KEYTEST'):])]
  semantic.update(editor_entered='messageBaseNewPost' in menus,typed_draft_sent=b'ABCDE' in sent,
   home_moves_before_marker=positions[:7]==[(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)],
   insert_toggles_overtype='OVR ' in clean)
  keys={'home':[b'\x1b[1~',b'\x1b[H',b'\x1bOH'],'end':[b'\x1b[4~',b'\x1b[F',b'\x1bOF'],
   'insert':[b'\x1b[2~'],'delete':[b'\x1b[3~'],'page_up':[b'\x1b[5~'],
   'page_down':[b'\x1b[6~'],'tab':[b'\t'],'delete_line':[b'\x19']}
  body=sent[sent.index(b'ABCDE'):]
  observed={name:[s.hex() for s in options if s in body] for name,options in keys.items()}
  assert all(observed.values()),observed
 else:
  data=(out/'RECV/PCXTEST.BIN').read_bytes()
  metadata=json.loads((out/'file-metadata.json').read_text())
  before_meta=metadata['before'];after_meta=metadata['after']
  assert len(before_meta)==len(after_meta)==1
  source=Path(before_meta[0]['filePath']).resolve()
  assert source.is_relative_to(ROOT/'build') and source.read_bytes()==data
  assert sha(source)==before_meta[0]['fileSha256']==after_meta[0]['fileSha256']
  assert after_meta[0]['meta']['dl_count']>=before_meta[0]['meta']['dl_count']+1
  assert {p.name for p in (out/'RECV').iterdir()}=={'PCXTEST.BIN'}
  decoders={d:Telnet() for d in ['to_bbs','from_bbs']};offsets={d:0 for d in decoders};trace=[]
  for event in json.loads((out/'chunk-trace.json').read_text()):
   direction=event['direction'];wire=(out/('to-bbs.bin' if direction=='to_bbs' else 'from-bbs.bin')).read_bytes()
   packet,_=decoders[direction].feed(wire[event['offset']:event['offset']+event['count']])
   if packet:trace.append(dict(direction='dos' if direction=='to_bbs' else 'bbs',offset=offsets[direction],size=len(packet),seconds=event['seconds']))
   offsets[direction]+=len(packet)
  assert trace==json.loads((out/'decoded-trace.json').read_text())
  protocol=audit_batch(display,{'PCXTEST.BIN':data})
  end_time=timestamp(trace,'bbs',protocol['end']-1)
  post=next(e for e in trace if e['direction']=='dos' and e['seconds']>end_time and b'S\r' in sent[e['offset']:e['offset']+e['size']+1])
  controls=audit_controls(protocol,sent,trace,'bbs',post['seconds'])
  assert controls and protocol['finish']
  semantic.update(complete_ZMODEM_protocol=True,exact_download=True,only_expected_downloads=True,
    official_download_counter_incremented=True,
    posttransfer_search_response='fileBaseSearch' in menus[menus.index('fileTransferProtocolSelection')+1:] and 'fileBaseListEntries' in menus[menus.index('fileTransferProtocolSelection')+1:])
 for name,value in semantic.items():assert report['checks'][name]==value,(name,value)
 assert report['passed']==all(report['checks'].values())
 return dict(evidence_audited=True,workflow_passed=report['passed'],route=report['route'],
  serial_payload_exact=True,display_payload_exact=True,authenticated=True,no_post_saved=True,
  semantic=semantic,observed_editor_keys=observed if report['route']=='editor' else None,
  auditor_sha256=sha(Path(__file__)),codec_sha256=sha(ROOT/'lab/bbs/modem.py'))


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
 print(json.dumps(audit(out),indent=2))
