#!/usr/bin/env python3
"""Read-only wire/serial/server/video audit; keep failed editor semantics failed."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from modem import Telnet

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
 else:
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
