#!/usr/bin/env python3
"""Extract the Help sub-gate from an exact, verified observer timeout image."""
import argparse,json,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);a=p.parse_args()
 folder=a.fixture.resolve();assert folder.is_relative_to(ROOT/'build')
 run=folder/'ordinary';snapshot=json.loads((run/'timeout-snapshot.json').read_text())
 assert snapshot['snapshot_verified'] and not snapshot['application_passed']
 image=run/'observer-memory.bin';raw=image.read_bytes()
 assert sha(image)==snapshot['observer_sha256_memory'] and sha(folder/'RENDER.COM')==snapshot['observer_sha256']
 replay=folder/'observer-replay.com';listing=folder/'observer-replay.lst'
 subprocess.run(['nasm','-fbin',str(folder/'observer.asm'),'-o',str(replay),'-l',str(listing)],check=True)
 assert replay.read_bytes()==(folder/'RENDER.COM').read_bytes()
 text=listing.read_text()
 def at(name):
  rows=re.findall(r'^\s*\d+ ([0-9A-F]{8}) .*\b'+name+r':',text,re.M)
  assert len(rows)==1,name
  return int(rows[0],16)+256
 def word(name):return int.from_bytes(raw[at(name):at(name)+2],'little')
 fields={n:word(n) for n in ('exec_seen','exec_done','child_exits','exit_code','hp_stage','hp_seed_failures','hp_help_seen','hp_serial_seen','hp_held_ticks','hp_frame_equal','hp_cursor_equal','nip_notice_status','nip_notice_cause','nip_notice_key','nip_notice_service','rp_find_seen','rp_next_line_seen','rp_next_topic_seen','rp_not_found_seen','rp_canceled_seen')}
 def chars(name,size):return raw[at(name):at(name)+size:2]
 wire=(run/'serial.bin').read_bytes()
 checks=dict(child_exited_zero=fields['exec_seen']==fields['exec_done']==fields['child_exits']==1 and fields['exit_code']==0,
  Help_sequence_complete=fields['hp_stage']==4 and fields['hp_seed_failures']==0,
  timer_paused=fields['hp_help_seen']==fields['hp_serial_seen']==1 and fields['hp_held_ticks']>=90,
  exact_popup_restore=fields['hp_frame_equal']==fields['hp_cursor_equal']==1,
  real_Help_pages=b'EXTERNAL PROGRAM / ERROR NOTICE' in chars('hp_help',4000) and b'SERIAL SESSION / LOCAL INPUT' in chars('hp_serial',4000),
  notice_receives_own_Enter=tuple(fields[n] for n in ('nip_notice_status','nip_notice_cause','nip_notice_key','nip_notice_service'))==(1,1,13,0),
  search_F3_nomatch_cancel=all(fields[n]==1 for n in fields if n.startswith('rp_')),
  search_captures=b'Receive files' in chars('rp_first',4000) and b'XMODEM' in chars('rp_first',4000) and b'Send files' in chars('rp_second',4000),
  real_next_EXEC=(run/'SUCCESS.OK').read_bytes()==b'OK',password_once=wire.count(b'Synth42\r')==1 and b'BAD' not in wire)
 result=dict(Help_subset_passed=all(checks.values()),application_passed=False,parent_keyboard_return_verified=False,
  fields=fields,checks=checks,parent_sha256=sha(run/'TERMINAL.EXE'),child_sha256=sha(run/'ASPECT.EXE'),
  receipts={str(p.relative_to(ROOT)):sha(p) for p in (run/'timeout-snapshot.json',image,folder/'observer.asm',folder/'RENDER.COM',listing,run/'serial.bin',run/'SUCCESS.OK')},
  extractor_sha256=sha(Path(__file__)),original_inputs=[],physical_verified=False,
  scope=__doc__+' Reassembled observer is byte-identical; exact source data-label offsets decode its captured allocation. Parent keyboard/menu/hangup still time out, so no complete application acceptance.')
 (folder/'Help-subset.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['Help_subset_passed'] else 1


if __name__=='__main__':raise SystemExit(main())
