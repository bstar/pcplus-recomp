#!/usr/bin/env python3
"""Production DOS menu/help, remote traffic and existing command-owner handoffs."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from test_connection_dos import run,ROOT,BINARY
from test_setup_startup_dos import run as run_setup,OUT as SETUP_OUT,EDITOR
from check_setup_model import image

def main():
 p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest==a.sha256
 out=ROOT/'build/command-menu-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
 observer=out/'MWATCH.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/command_menu_watch.asm'),'-o',str(observer)],check=True)
 cases=[]
 def terminal_case(suffix,keys,updates,mode='success'):
  name='menu-'+a.label+'-'+suffix;folder=ROOT/'build/connection-dos'/name
  assert not folder.exists(),'Fresh owned case required'
  result=run(name,mode,keys,working_drive='d',files={'MWATCH.COM':observer.read_bytes()},observer='MWATCH',online_updates=updates)
  return result,folder
 result,folder=terminal_case('browse',
  'p3000 a-z p600 right p600 right p600 f1 p600 / i n t e r v a l enter p600 escape p600 escape p700 r e a d y p400 a-x',
  [(4.2,b'\x1b[5;1HBACKGROUND\x1b[6n')])
 raw=(folder/'MVIEW.BIN').read_bytes();assert len(raw)==10246
 magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4d43 and count<=32
 frames=[raw[6+i*320:6+(i+1)*320] for i in range(count)]
 wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
 result['checks'].update(independent_menu_observer=ticks>5,
  file_menu_observed=any(b'Receive files' in f[:80] for f in frames),
  connection_menu_observed=any(b'Dial selected target' in f[:80] for f in frames),
  view_menu_observed=any(b'Redisplay history' in f[:80] for f in frames),
  contextual_history_help_observed=any(b'Browse a frozen' in f[160:240] for f in frames),
  help_search_finds_BREAK_prose=any(b'Drain outgoing' in f[160:240] for f in frames),
  continued_actual_CPR=b'\x1b[5;11R' in wire,
  local_search_and_arrows_not_transmitted=b'interval' not in wire and b'\x1b[C' not in wire,
  updated_live_screen_restored=screen[640:660:2]==b'BACKGROUND',post_menu_keyboard=b'ready' in wire)
 result['passed']=all(result['checks'].values());result['observed_frames']=[f.decode('cp437') for f in frames];cases.append(result)
 result,folder=terminal_case('actions',
  'p3000 a-z o p300 enter p2000 a-z h p500 a-z h p500 a-z w p500 a-z o p500 a-z r p500 escape p500 a-z s p500 escape p500 a-z right h p2200 a-z right d p2500 r e a d y p500 a-x',
  [(4.2,b'\x1b[7;1HCAPTURELINE\r\n')],mode='hangup')
 log=(folder/'PCPLUS.LOG').read_bytes();snapshot=(folder/'PCPLUS.SCR').read_bytes();wire=(folder/'serial.bin').read_bytes()
 result['checks'].update(exact_processed_capture=log==b'CAPTURELINE\r\n',
  snapshot_contains_live_screen=b'CAPTURELINE' in snapshot,
  snapshot_does_not_capture_menu=b'Command Menu' not in snapshot and b'Receive files' not in snapshot,
  canceled_prompts_emit_no_handshake=b'\x15' not in wire and b'\x18' not in wire,
  menu_hangup_then_new_configured_dial=result['commands']==['ATZ','ATDCaseTest:23','ATZ','ATDCaseTest:23'],
  post_command_keyboard=b'ready' in wire)
 result['passed']=all(result['checks'].values());result['capture_hex']=log.hex();cases.append(result)
 name='menu-settings-'+a.label;assert not (SETUP_OUT/name).exists()
 result,actual=run_setup(name,keys='p2000 a-z right right right enter p600 escape p500 space p500 a-z p500 escape r e a d y',arguments='@TEST.PRM',post_echo=True)
 result['checks'].update(canceled_editor_preserves_exact_PRM=actual==image(),
  keyboard_after_child_and_reopened_menu=b'ready' in (SETUP_OUT/name/'serial.bin').read_bytes())
 result['passed']=all(result['checks'].values());cases.append(result)
 result,folder=terminal_case('split-parser',
  'p2000 a-z p300 right p300 right p1500 escape p500 r e a d y p500 a-x',
  [(.4,b'\x1b['),(2.1,b'31mPARTIAL\r\n\x1b[6n')])
 raw=(folder/'MVIEW.BIN').read_bytes();assert len(raw)==10246
 magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4d43 and count<=32
 frames=[raw[6+i*320:6+(i+1)*320] for i in range(count)]
 wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
 result['checks'].update(menu_observed_after_split=ticks>5 and any(b'Redisplay history' in f[:80] for f in frames),
  queued_arrows_stay_local=b'\x1b[C' not in wire,parser_finishes_and_replies=b'\x1b[2;1R' in wire,
  live_partial_text_restored=b'PARTIAL' in screen[::2],ordinary_keyboard_after_menu=b'ready' in wire)
 result['passed']=all(result['checks'].values());result['observed_frames']=[f.decode('cp437') for f in frames];cases.append(result)
 for case in cases:
  (out/(case.get('case',case.get('name','case'))+'.json')).write_text(json.dumps(case,indent=2)+'\n')
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=digest,editor_sha256=hashlib.sha256(EDITOR.read_bytes()).hexdigest(),cases=cases,
  sources={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in ['standalone/test_command_menu_dos.py','standalone/command_menu_watch.asm','standalone/test_connection_dos.py','standalone/test_setup_startup_dos.py','src/redisplay/command_menu.c','src/redisplay/command_menu.h','src/redisplay/redisplay.c','src/terminal/redisplay.asm']},
  scope='Actual production DOS menu/help with independent timer/video observer, remote updates/replies, processed capture and screen file, canceled transfer prompts, hangup/redial, real PRMEDIT child and parser-split deferred entry. No product state observed by this harness. Synthetic owned fixtures; no physical modem or original menu equivalence.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']

if __name__=='__main__':main()
