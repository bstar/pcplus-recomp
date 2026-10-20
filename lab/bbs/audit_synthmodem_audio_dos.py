#!/usr/bin/env python3
"""Read-only wire and DOS artifact audit for the complete audio/BBS cohort."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from modem import Telnet
from synthmodem_gateway import records

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);a=p.parse_args();out=a.cohort.resolve()
 r=json.loads((out/'result.json').read_text());n=json.loads((out/'node-result.json').read_text())
 checks={};serial=(out/'serial-in.bin').read_bytes();wire=(out/'control-wire.bin').read_bytes();at=0;data=bytearray();status=[]
 while at<len(wire):
  assert at+3<=len(wire);size,kind=struct.unpack_from('<HB',wire,at);assert 1<=size<=4094 and at+size+2<=len(wire)
  b=wire[at+3:at+size+2];at+=size+2
  if kind==0x15:data.extend(b)
  elif kind==0x13:status.append(json.loads(b))
 prefix=b'ATZ\rATD1\r';checks['numeric_command_prefix']=serial.startswith(prefix) and n['commands']==['ATZ','ATD1']
 # The production session deliberately discards post-training tail bytes while
 # its proxy is detached. Account for that exact sink count, never arbitrary
 # mismatching bytes from the online stream. Preserve the prefix in the report.
 holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(out/'node.log').read_text())
 checks['single_normal_post_train_hold']=len(holds)==1 and 6000<=int(holds[0][0])<=15500
 dropped=int(holds[0][1]) if len(holds)==1 else 0
 online=serial[len(prefix):];checks['serial_equals_post_hold_guest_decode']=online==data[dropped:]
 target=online.split(b'\r',1)[0]+b'\r';checks['online_target_after_numeric_call']=bool(re.fullmatch(rb'127\.0\.0\.1:\d+\r',target))
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 checks['guest_equals_Telnet_application_input']=bytes(data[dropped:])==target+sent
 caller=(out/'caller-decoded.bin').read_bytes()
 checks['decoded_audio_equals_serial_output']=(out/'serial-out.bin').read_bytes()==b'\r\nOK\r\n\r\nCONNECT 1200\r\n'+caller
 display_at=caller.find(display) if display else -1
 checks['complete_BBS_display_survives_DSP']=display_at>=0
 checks['single_real_carrier']=sum(s.get('event')=='connect' and s.get('rate')==1200 for s in status)==1
 checks['real_DOS_terminal_replies']=b'\x1b[?1;2c' in sent and bool(re.search(rb'\x1b\[\d+;\d+R',sent))
 rows=[json.loads(b) for b in (out/'server-session.jsonl').read_text().splitlines()]
 checks['authoritative_login']=sum(v.get('msg')=='User "loclab" successfully logged in' for v in rows)==1
 menus=[v['menuName'] for v in rows if v.get('menuName')];wanted=['mainMenu','messageBaseMainMenu','mainMenu','fileBaseMainMenu'];index=0
 for m in menus:
  if index<len(wanted) and m==wanted[index]:index+=1
 checks['authoritative_menu_order']=index==len(wanted)
 checks['script_and_normal_DOS_return']=(out/'SCRIPT.OK').is_file() and (out/'SCRIPT.OK').read_bytes()==b'PASS' and (out/'PASS.TXT').is_file() and not (out/'FAIL.TXT').exists()
 def read(name):return (out/name).read_bytes() if (out/name).is_file() else b''
 checks['actual_UART_restored']=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN')
 checks['keyboard_timer_vector_restored']=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN')
 for name in ('rtp-from-answer.bin','rtp-from-caller.bin'):
  headers=[]
  for b in records((out/name).read_bytes()):
   assert len(b)==172 and b[0]==0x80 and b[1]&127==0;headers.append(struct.unpack_from('>HII',b,2))
  checks['continuous_'+name]=bool(headers) and all(seq==(headers[0][0]+i)%65536 and ts==(headers[0][1]+160*i)%2**32 and ssrc==headers[0][2] for i,(seq,ts,ssrc) in enumerate(headers))
 requests=records((out/'sip-to-server.bin').read_bytes());responses=records((out/'sip-to-caller.bin').read_bytes())
 checks['actual_external_SIP']=any(b.startswith(b'INVITE ') for b in requests) and any(b.startswith(b'ACK ') for b in requests) and any(b.startswith(b'BYE ') for b in responses) and any(b.startswith(b'SIP/2.0 200') and b' BYE\r\n' in b for b in requests)
 checks['actual_internal_BYE']='Response msg 200/BYE' in (out/'qemu-0.log').read_text()
 checks['capture_hashes']=all(sha(out/name)==h for name,h in r['captures_sha256'].items())
 result={'passed':all(checks.values()),'checks':checks,'producer_sha256':sha(out/'result.json'),
  'auditor_sha256':sha(Path(__file__)),'payloads':{'BBS_input_bytes':len(sent),'BBS_display_bytes':len(display),
   'BBS_input_sha256':hashlib.sha256(sent).hexdigest(),'BBS_display_sha256':hashlib.sha256(display).hexdigest(),
   'display_offset_in_caller':display_at,'guest_DATA_RX_bytes':len(data),'pre_proxy_training_tail_bytes':dropped,
   'pre_proxy_training_tail_hex':bytes(data[:dropped]).hex(),'unadjusted_serial_guest_identity':online==data},
  'scope':'Independent read-only actual DOS/ASPECT, BBS authoritative logs, guest frames, serial/Telnet byte identity, RTP continuity, SIP and cleanup audit. No physical modem/ATA claim.'}
 (out/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
