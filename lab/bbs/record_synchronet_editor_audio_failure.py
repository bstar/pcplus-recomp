#!/usr/bin/env python3
"""Seal the first Synchronet editor run with its incomplete final-screen drain."""
import argparse,hashlib,json
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,sha
from modem import Telnet


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 assert not r['passed'] and r['peer']=='synchronet'
 assert r['route']=='editor-abort'
 assert {k for k,v in r['checks'].items() if not v}=={'final_DOS_main_menu','no_gateway_errors'}
 assert not base['passed'] and {k for k,v in base['checks'].items() if not v}=={'complete_BBS_display_survives_DSP','complete_caller_stream_equals_bridge_plus_BBS_display'}
 assert io['evidence_consistent'] and all(io['checks'].values())
 assert base['checks']['exact_editor_and_abort_keyboard_input'] and all(base['editor'].values())
 assert r['script_stages']=='BRIDGE|LOGIN|PASSWORD|WELCOME|BULLETINS|SCAN|PAUSE|MAIN|SUBJECT|EDITOR|'
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
 caller=(out/'caller-decoded.bin').read_bytes();expected=bridge+display
 assert expected.startswith(caller) and len(expected)-len(caller)==1011
 assert r['checks']['DOS_normal_exit'] and r['checks']['UART_and_IRQ_PIC_restored'] and r['checks']['keyboard_timer_restored']
 assert r['gateway']['errors']==['read ECONNRESET']
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json']))
 result={'passed':False,'actual_Synchronet_audio_accepted':False,'cohort':str(out.relative_to(ROOT)),
  'failure':'Editor key semantics and Ctrl-Q abort pass, but the BIOS helper exits after a fixed20-second final delay while the3500-byte Main screen is still arriving over1200bps audio. Caller is an exact prefix missing1011 display bytes; original whole-display and final-screen gates remain failed. Frontend read ECONNRESET is retained, not waived.',
  'source_checkpoint':'5fe8fac','producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],
  'exact_online_bytes':len(online),'BBS_input_bytes':len(sent),'BBS_display_bytes':len(display),'caller_bytes':len(caller),'missing_display_suffix_bytes':1011,'caller_is_exact_bridge_display_prefix':True,
  'editor':base['editor'],'serial_counters':io['counters'],'error_events':io['error_events'],'hardware_snapshot':base['hardware_snapshot'],'script_stages':r['script_stages'],
  'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'Failed first actual Synchronet editor audio/DOS test. Exact130 online native/offline/guest/BBS bytes and all nine editor semantics hold. No saved messages or modified code/config/body bytes. Normal DOS/UART/PIC/IRQ/timer/SIP restoration. Preserve all failed whole-display/final-screen/gateway gates. Rerun using actual rendered final-main/footer observation; no software or physical acceptance granted.'}
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'failed_editor_drain_preserved':True,'exact_online_bytes':len(online),'BBS_display_bytes':len(display),'receipt':str(target)}))

if __name__=='__main__':main()
