#!/usr/bin/env python3
"""Independent Synchronet full transport, XMODEM upload and cleanup audit."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from modem import Telnet
from synthmodem_gateway import records

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cancel_protocol(sent,display,trace,expected):
 from test_transfer_dos import packet_at,timestamp
 import binascii
 frames=[];first=None
 for at in range(len(sent)):
  item=packet_at(sent,at,True)
  if item and item['number']==1 and item['payload']==expected[:item['size']]:first=at;break
 assert first is not None,'No valid first CRC frame'
 assert sent.endswith(b'\x18\x18 Q'),'Require native CAN pair followed by actual Space/Q menu input'
 cancel=len(sent)-4;at=first;offset=0;number=1
 while at<cancel:
  item=packet_at(sent,at,True)
  if not item:break
  assert item['number']==number and item['payload']==expected[offset:offset+item['size']]
  frames.append({k:v for k,v in item.items() if k!='payload'});offset+=item['size'];number+=1;at=item['end']
 assert frames and offset<len(expected),'Cancellation must follow progress but precede completion'
 tail=sent[at:cancel]
 assert not tail,'Fixed sender must cancel after a complete checksum/CRC frame'
 if tail:
  size=1024 if len(expected)-offset>=1024 else 128;body=expected[offset:offset+size].ljust(size,b'\x1a')
  next_frame=bytes([2 if size==1024 else 1,number,255-number])+body+binascii.crc_hqx(body,0).to_bytes(2,'big')
  assert len(tail)<len(next_frame) and next_frame.startswith(tail),'Unaccounted pre-CAN tail'
 # Complete frame/prefix/CAN decomposition leaves no EOF or fabricated success.
 when=timestamp(trace,'dos',cancel);banner=display.index(b'Start XMODEM-1K/CRC transfer now')
 ack=display.index(b'\x06',banner);ack_when=timestamp(trace,'bbs',ack)
 assert timestamp(trace,'dos',frames[0]['end']-1)<=ack_when<when,'Cancellation must follow real received ACK'
 post_time=timestamp(trace,'dos',cancel+2);assert when<post_time
 return dict(frames=frames,complete_source_bytes=offset,incomplete_next_frame_bytes=len(tail),incomplete_next_frame_sha256=hashlib.sha256(tail).hexdigest(),cancel_offset=cancel,first_ACK_offset=ack,first_ACK_seconds=ack_when,cancel_seconds=when,post_input_seconds=post_time)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);a=p.parse_args();out=a.cohort.resolve()
 r=json.loads((out/'result.json').read_text());n=json.loads((out/'node-result.json').read_text())
 assert r['peer']=='synchronet' and r['posttrain_hold']
 from audio_synchronet import snapshot,message_bodies
 from synchronet import Peer
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
 # Require the entire caller stream, including the bridge preamble and EOF.
 # A substring match alone could hide extra decoded bytes before/after display.
 # CRCRLF is the bridge's current _sendLine behavior, retained explicitly here.
 address=target[:-1]
 bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+address+b'...\r\r\nConnected to '+address+
  b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
 checks['complete_caller_stream_equals_bridge_plus_BBS_display']=caller==bridge+display
 checks['single_real_carrier']=sum(s.get('event')=='connect' and s.get('rate')==1200 for s in status)==1
 checks['real_DOS_terminal_replies']=b'\x1b[?1;2c' in sent and bool(re.search(rb'\x1b\[\d+;\d+R',sent))
 clean=Peer.cleaned(display)
 tokens=['Login:','Password:','Read/Post Messages','List Files in dir','Which, Quit','PCPlus Lab:','Filename:','to Main PCPlus Lab?','Enter a description now.','Protocol, Batch','Hang up after transfer?','[Hit a key]','List Files in dir','Read/Post Messages']
 cursor=0;ordered=True
 for token in tokens:
  found=clean.find(token,cursor)
  if found<0:ordered=False;break
  cursor=found+len(token)
 checks['ordered_actual_Synchronet_prompts']=ordered
 checks['one_authoritative_synthetic_login']=len(re.findall(rb'LABUSER\s+Logon ',(out/'server-session.log').read_bytes()))==1
 from audio_synchronet_cancel_fixed import NAME,AREA,payload,stored_files
 from audit_audio_download import frontend_trace
 expected=payload(NAME);protocol=None;errors=[]
 checks.update(CRC_progress_ACK_before_CAN=False,no_EOT_or_complete_upload=False,exact_menu_and_protocol_input=False,retained_partial_accounted=False)
 try:
  timing,provenance=frontend_trace(out,sent,display,len(bridge))
  protocol=cancel_protocol(sent,display,timing,expected)
  first=protocol['frames'][0]['offset'];at=protocol['cancel_offset']
  checks['CRC_progress_ACK_before_CAN']=True
  checks['CAN_at_complete_packet_boundary']=protocol['incomplete_next_frame_bytes']==0
  checks['no_EOT_or_complete_upload']=True
  initial=re.sub(rb'\x1b\[(?:\?1;2c|\d+;\d+R)',b'',sent[:first])
  checks['exact_menu_and_protocol_input']=initial==b'LABUSER\rLABPASS42\r Qn\r TJ11\rUSXCAN002.BIN\rySynthetic PCPlus audio cancel\r1n' and sent[at:]==b'\x18\x18 Q'
  target=AREA/NAME;partial=target.read_bytes() if target.exists() else b''
  checks['retained_partial_accounted']=expected.startswith(partial) and len(partial)<len(expected) and len(partial)<=protocol['complete_source_bytes']
  protocol['retained_bytes']=len(partial)
 except Exception as error:errors.append(repr(error))
 files=stored_files();before_files=r['upload']['existing_files_before']
 checks['existing_files_preserved']=all(files.get(n)==h for n,h in before_files.items())
 checks['only_expected_new_server_file']=set(files)==set(before_files)|{NAME}
 source=Path(__file__).resolve().parents[2]/r['upload']['source_path']
 checks['synthetic_source_unchanged']=source.read_bytes()==expected and sha(source)==r['upload']['source_sha256']
 checks['no_unrecognized_commands']='Unrecognized command' not in clean
 checks['message_bodies_unchanged']=message_bodies()==r['message_bodies']
 before_stats=r['statistics_before']['Total'];after_stats=r['statistics_after']['Total']
 checks['no_message_mail_or_download_writes']=all(before_stats[k]==after_stats[k] for k in ('dnloads','dnloadb','posts','email','feedback'))
 editor=None
 checks['script_and_normal_DOS_return']=(out/'SCRIPT.OK').is_file() and (out/'SCRIPT.OK').read_bytes()==b'PASS' and (out/'PASS.TXT').is_file() and not (out/'FAIL.TXT').exists()
 def read(name):return (out/name).read_bytes() if (out/name).is_file() else b''
 before=read('BEFORE.BIN');after=read('AFTER.BIN');snapshots_valid=len(before)==len(after)==42
 # Keep the original42-byte aggregate gate. The independent sampler includes
 # IRQ vectors0x08..0x0f, the test helper's INT1C vector, then six UART/PIC bytes.
 # Report those parts separately so a helper retirement failure is not mistaken
 # for a UART register-cleanup defect.
 checks['actual_UART_restored']=snapshots_valid and before==after
 checks['actual_IRQ_vectors_restored']=snapshots_valid and before[:32]==after[:32]
 checks['actual_UART_PIC_restored']=snapshots_valid and before[36:]==after[36:]
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
 root=Path(__file__).resolve().parents[2]
 checks['runtime_inputs_unchanged']=all(sha(Path(name))==h for name,h in r['runtime_inputs'].items())
 checks['producer_inputs_unchanged']=all(sha(root/name)==h for name,h in r['frozen_inputs'].items())
 if r.get('input_sequence_timeout_ms',0):
  checks['explicit_key_framing_configuration']=r['input_sequence_timeout_ms']==250 and n.get('inputSequenceTimeoutMs')==250
  checks['pinned_Synchronet_inputs_unchanged']=snapshot()==r['server']
 result={'passed':all(checks.values()),'checks':checks,'producer_sha256':sha(out/'result.json'),
  'auditor_sha256':sha(Path(__file__)),'audit_inputs':{name:sha(root/name) for name in ('lab/bbs/audit_synchronet_cancel_fixed_audio_dos.py','lab/bbs/audio_synchronet.py','lab/bbs/audio_synchronet_cancel_fixed.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_audio_download.py','lab/bbs/synchronet.py','lab/bbs/modem.py','lab/bbs/synthmodem_gateway.py')},'payloads':{'BBS_input_bytes':len(sent),'BBS_display_bytes':len(display),
   'BBS_input_sha256':hashlib.sha256(sent).hexdigest(),'BBS_display_sha256':hashlib.sha256(display).hexdigest(),
   'display_offset_in_caller':display_at,'expected_bridge_bytes':len(bridge),'full_caller_sha256':hashlib.sha256(caller).hexdigest(),'guest_DATA_RX_bytes':len(data),'pre_proxy_training_tail_bytes':dropped,
   'pre_proxy_training_tail_hex':bytes(data[:dropped]).hex(),'unadjusted_serial_guest_identity':online==data},
  'hardware_snapshot':{'layout':'32 IRQ-vector bytes,4 INT1C bytes,6 UART/PIC bytes','INT1C_restored':snapshots_valid and before[32:36]==after[32:36],
   'differing_offsets':[i for i,(a,b) in enumerate(zip(before,after)) if a!=b] if snapshots_valid else None},
  'protocol':protocol,'protocol_errors':errors,'server_partial_cleanup_accepted':not (AREA/NAME).exists(),'scope':'Independent actual DOS Escape cancellation after verified CRC/ACK progress, no EOF/full-source success, complete retained-prefix accounting, actual Files/Main interaction, guest frames, serial/Telnet byte identity, RTP continuity, SIP and cleanup audit. No physical modem/ATA claim.'}
 (out/'independent-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
