#!/usr/bin/env python3
"""Audit actual DOS editor draft captures; normal DOS exit is insufficient."""
import argparse,hashlib,json,re
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def audit(name,label,expect_page_down=True,disconnect=False,keyboard_profile='network'):
 out=ROOT/'build/bbs-lab/results'/name/label
 result=json.loads((out/'result.json').read_text());tx=(out/'serial-received.bin').read_bytes();display=(out/'display.bin').read_bytes()
 clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437',errors='replace')
 keys={'home':[b'\x1b[1~',b'\x1b[H',b'\x1bOH'],'end':[b'\x1b[4~',b'\x1b[F',b'\x1bOF'],'insert':[b'\x1b[2~'],'delete':[b'\x1b[3~'],'page_up':[b'\x1b[5~'],'page_down':[b'\x1b[6~'],'tab':[b'\t'],'delete_line_ctrl_y':[b'\x19']}
 if keyboard_profile=='enigma-editor':
  assert name=='enigma' and result.get('keyboard_profile'),'Explicit ENiGMA KBD run required'
  kbd=(out/'BOARD.KBD').read_bytes()
  assert hashlib.sha256(kbd).hexdigest()==result['keyboard_profile']['sha256']
  for profile in (4,6):
   for slot,value in ((8,22),(54,22),(56,1),(76,1),(57,5),(77,5)):
    assert kbd[profile*948+slot*12:profile*948+(slot+1)*12]==bytes([value])+bytes(11)
  keys.update(home=[b'\x01'],end=[b'\x05'],insert=[b'\x16'])
  assert b'ABCDE' in tx,'No measured editor body'
  tx=tx[tx.index(b'ABCDE'):]
 observed={key:any(s in tx for s in options) for key,options in keys.items()}
 checks={'DOS_harness':result['passed'],'typed_draft_sent':b'ABCDE' in tx,'all_exercised_keys_emitted':all(value for key,value in observed.items() if expect_page_down or key!='page_down')}
 authority={}
 if name=='enigma':
  start=json.loads((out/'server-log-start.json').read_text())['byte_offset'];log=ROOT/'build/bbs-lab/enigma/source/logs/enigma-bbs.log'
  with log.open('rb') as f:f.seek(start);rows=[json.loads(x) for x in f if x.strip()]
  rows=[r for r in rows if datetime.fromisoformat(r['time'].replace('Z','+00:00')).timestamp()<=(out/'result.json').stat().st_mtime]
  sessions={r['sessionId'] for r in rows if r.get('menuName')=='telnetConnected'};assert len(sessions)==1,sessions
  session=sessions.pop();rows=[r for r in rows if r.get('sessionId')==session];menus=[r['menuName'] for r in rows if r.get('menuName')]
  entered='messageBaseNewPost' in menus;left=entered and 'messageBaseMainMenu' in menus[menus.index('messageBaseNewPost')+1:]
  checks.update(stock_editor_entered=entered,no_post_saved=not any('posted message to' in r.get('msg','') for r in rows),insert_toggled_overtype='OVR ' in clean)
  body=clean[clean.find('KEYTEST'):]
  positions=[(int(row),int(col)) for row,col in re.findall(r'(?:INS|OVR) (\d+),(\d+)',body)]
  checks['home_moves_before_marker']=positions[:7]==[(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)]
  if not disconnect:checks['discard_returned_message_menu']=left
  authority={'session_id':session,'menus':menus,'first_body_cursor_positions':positions[:20]};(out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 else:
  csi=rb'\x1b\[[0-?]*[ -/]*[@-~]'
  checks.update(stock_editor_entered='FSEditor v1.105' in clean,draft_aborted='Aborted.' in clean,insert_toggled_overtype='Overwrite Mode' in clean,
   home_marker_at_line_start=b'\x1b[5;1HHABCDE' in display,end_marker_at_line_end=b'\x1b[5;7HE' in display,
   delete_erases_final_character=b'\x1b[5;7H\x1b[5;7H\x1b[K' in display,
   tab_advances_to_next_stop=b'\x1b[5;8H \x1b[5;9H' in display,
   page_keys_report_document_boundaries=bool(re.search(b'T'+b'(?:'+csi+b')*'+b'\x07'+b'(?:'+csi+b')*'+b'\x07',display)),
   ctrl_y_delete_line_response=b'\x1b[M' in display and 'unsupported terminal' not in clean.lower())
 audit={'passed':all(checks.values()),'checks':checks,'observed_key_wire':observed,'binary_sha256':result['binary_sha256'],'serial':result['serial'],'authority':authority,'scope':'Actual loopback stock editor draft and captured DOS keyboard wire. Draft discard/abort attempted; inspect no_post_saved or draft_aborted before claiming successful cancellation. One-line page keys test wire emission and boundary handling only; no multiline scrolling or physical UART claim.','exit_mode':'close_unsaved_connection' if disconnect else 'editor_discard_or_abort','unexercised_keys':[] if expect_page_down else ['page_down (invalid ADDKEY pgdn alias; rerun with pgdown)']}
 audit['modem_packet_delay_ms']=result.get('modem_packet_delay_ms',0)
 audit['keyboard_profile']=keyboard_profile
 if audit['modem_packet_delay_ms']:audit['scope']+=' Explicit modem buffering experiment; does not replace immediate-bridge failures or prove physical firmware compatibility.'
 (out/'semantic-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2));return audit['passed']
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name',choices=['enigma','synchronet']);p.add_argument('--label',required=True);p.add_argument('--page-down-not-exercised',action='store_true');p.add_argument('--disconnect-unsaved',action='store_true');p.add_argument('--keyboard-profile',choices=['network','enigma-editor'],default='network');a=p.parse_args();raise SystemExit(0 if audit(a.name,a.label,not a.page_down_not_exercised,a.disconnect_unsaved,a.keyboard_profile) else 1)
