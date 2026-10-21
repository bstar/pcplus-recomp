#!/usr/bin/env python3
"""Seal the first Synchronet recipe failure without accepting its missing route."""
import argparse,hashlib,json
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,sha
from modem import Telnet


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 assert not r['passed'] and r['peer']=='synchronet'
 assert {k for k,v in r['checks'].items() if not v}=={'script_completed','ordered_script_stages','real_bulletin_statistics','file_and_empty_message_navigation','final_DOS_main_menu'}
 assert not base['passed'] and {k for k,v in base['checks'].items() if not v}=={'complete_caller_stream_equals_bridge_plus_BBS_display','ordered_actual_Synchronet_prompts','owned_empty_local_message_area','exact_read_only_navigation_input','script_and_normal_DOS_return'}
 assert io['evidence_consistent'] and all(io['checks'].values())
 assert r['script_stages']=='BRIDGE|LOGIN|PASSWORD|WELCOME|FAIL-BULLETINS|'
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(out/n)==h,n
 assert snapshot()==r['server'] and message_bodies()==r['message_bodies']
 serial=(out/'serial-in.bin').read_bytes();prefix=b'ATZ\rATD1\r';assert serial.startswith(prefix);online=serial[len(prefix):]
 offline=bytes.fromhex(''.join(c['hex'] for c in read('offline-caller.json')['received']));assert online==offline
 wire=(out/'control-wire.bin').read_bytes();at=0;guest=bytearray()
 while at<len(wire):
  size=int.from_bytes(wire[at:at+2],'little');assert size>=1 and at+size+2<=len(wire)
  if wire[at+2]==0x15:guest.extend(wire[at+3:at+size+2])
  at+=size+2
 assert online==guest
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 address=online.split(b'\r',1)[0];assert online==address+b'\r'+sent
 bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+address+b'...\r\r\nConnected to '+address+b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
 tail=b'\r\r\nConnection closed by remote host.\r\r\n\r\r\nCONNECT> '
 assert (out/'caller-decoded.bin').read_bytes()==bridge+display+tail
 assert sent[sent.index(b'LABPASS42\r')+len(b'LABPASS42\r'):]==b' '
 literal=b'Enter number of bulletin or [Quit]';stable=b'Enter number of bulletin or ['
 assert literal not in display and stable in display
 prompt=display[display.index(stable):display.index(stable)+len(stable)+40]
 assert b'\x1b[' in prompt and b'uit]' in prompt
 recipe_path=ROOT/'build/bbs-lab/synchronet-audio-recipe-check-01/result.json';recipe=json.loads(recipe_path.read_text())
 assert not recipe['passed'] and [c['phase'] for c in recipe['cases'] if not c['raw_match_possible']]==['bulletins','statistics']
 for n,h in recipe['inputs'].items():assert sha(ROOT/n)==h,n
 assert r['checks']['DOS_normal_exit'] and r['checks']['UART_and_IRQ_PIC_restored'] and r['checks']['keyboard_timer_restored']
 assert not r['gateway']['errors']
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json']))
 result={'passed':False,'actual_Synchronet_audio_accepted':False,'cohort':str(out.relative_to(ROOT)),
  'failure':'ASPECT waits for visible [Quit] as a literal raw token, but Synchronet inserts ANSI SGR inside that word. Script reaches the real bulletin menu but times out; idle server disconnect follows before the configured BIOS watchdog exits normally.',
  'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],
  'exact_online_bytes':len(online),'BBS_input_bytes':len(sent),'exact_BBS_display_bytes':len(display),'extra_caller_bytes_hex':tail.hex(),
  'caller_stream_equals_explicit_bridge_display_close_tail':True,'raw_colored_prompt_hex':prompt.hex(),'raw_literal_needle_absent':True,'stable_prefix_present':True,
  'actual_CPR_values':__import__('re').findall(r'\x1b\[(\d+);(\d+)R',sent.decode('latin1')),
  'recipe_diagnostic_sha256':sha(recipe_path),'server_binary_sha256':r['server']['binary_sha256'],'server_source_commit':r['server']['source_commit'],
  'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],'script_stages':r['script_stages'],
  'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'Failed first actual Synchronet audio/DOS route, retained unchanged. All57 online bytes match native/offline/guest/BBS input; all10542 BBS display bytes and exact source-defined remote-close/menu suffix survive the caller stream. No gateway errors and normal native hardware/timer cleanup hold. These positive diagnostics do not waive the missing bulletin/file/message/final-main workflow or the original failed whole-caller gate. Correct raw needles and rerun every original gate on fresh evidence. Editors/transfers, pressure/loss, physical and F01-F16 remain open.'}
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'recipe_failure_preserved':True,'exact_online_bytes':len(online),'BBS_display_bytes':len(display),'receipt':str(target)}))

if __name__=='__main__':main()
