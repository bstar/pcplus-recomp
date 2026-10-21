#!/usr/bin/env python3
"""Seal exact stock Synchronet XMODEM upload audio/DOS workflow at its tested scope."""
import argparse,hashlib,json,re
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,sha
from modem import Telnet
from synthmodem_posttrain_validation import validate as validate_runtime


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 assert r['peer']=='synchronet' and r['route']=='xmodem-upload' and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
 for data in (r,base,io):assert data.get('passed',data.get('evidence_consistent')) and all(data['checks'].values())
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(out/n)==h,n
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 assert sha(out/'program/ASPECT.EXE')==r['frozen_inputs']['build/aspect-runner/ASPECT.EXE']
 runtime=Path(next(iter(r['runtime_inputs'])))
 runtime=next(p for p in runtime.parents if (p/'source/config.js').is_file());assert validate_runtime(runtime)==r['runtime_inputs']
 assert snapshot()==r['server'] and message_bodies()==r['message_bodies']
 for k in ('dnloads','dnloadb','posts','email','feedback'):assert r['statistics_before']['Total'][k]==r['statistics_after']['Total'][k]
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix);online=serial[len(prefix):]
 offline=bytes.fromhex(''.join(c['hex'] for c in read('offline-caller.json')['received']));assert online==offline
 raw=(out/'control-wire.bin').read_bytes();at=0;guest=bytearray()
 while at<len(raw):
  size=int.from_bytes(raw[at:at+2],'little');assert size>=1 and at+size+2<=len(raw)
  if raw[at+2]==0x15:guest.extend(raw[at+3:at+size+2])
  at+=size+2
 assert online==guest
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());address=online.split(b'\r',1)[0]
 assert online==address+b'\r'+sent
 bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+address+b'...\r\r\nConnected to '+address+b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
 assert (out/'caller-decoded.bin').read_bytes()==bridge+display
 holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(out/'node.log').read_text());assert len(holds)==1 and 6000<=int(holds[0][0])<=15500 and holds[0][1]=='0'
 prerequisites={n:h for n,h in r['frozen_inputs'].items() if n.endswith('/result.json')};assert len(prerequisites)==4
 for n in prerequisites:assert json.loads((ROOT/n).read_text())['passed']
 recipe=[json.loads((ROOT/n).read_text()) for n in prerequisites if 'recipe' in n];assert len(recipe)==1 and all(c['raw_match_possible'] for c in recipe[0]['cases'])
 timing=read('upload-control-timing.json');assert timing['passed'] and all(timing['checks'].values())
 for n,h in timing['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in timing['captures_sha256'].items():assert sha(out/n)==h,n
 metadata=read('upload-metadata-audit-v2.json');assert metadata['passed'] and all(metadata['checks'].values())
 original=read('upload-metadata-audit.json');assert not original['passed'] and {k for k,v in original['checks'].items() if not v}=={'helper_full_receive_zero_errors'}
 assert metadata['original_audit_sha256']==sha(out/'upload-metadata-audit.json')
 assert (metadata['startup_requests'],metadata['startup_timeouts'],metadata['data_block_errors'])==(4,3,0)
 for n,h in metadata['source_authority'].items():assert sha(ROOT/n)==h,n
 for n,h in metadata['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in metadata['captures_sha256'].items():assert sha(out/n)==h,n
 from audio_synchronet_upload import NAME,AREA,payload,stored_files
 source=ROOT/r['upload']['source_path'];assert sha(source)==r['upload']['source_sha256'] and source.read_bytes()==payload(NAME)
 assert (AREA/NAME).read_bytes()==(out/'receiver-installed.bin').read_bytes()==payload(NAME)+b'\x1a'*127
 assert sha(AREA/NAME)==r['upload']['stored_sha256']
 assert all(stored_files().get(n)==h for n,h in r['upload']['existing_files_before'].items())
 assert len(base['protocol']['frames'])==base['protocol']['accepted_blocks']==14 and base['protocol']['crc']
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json','server-inputs.json','SEND/SXAUDIO1.BIN','receiver-installed.bin','upload-control-timing.json','upload-metadata-audit.json','upload-metadata-audit-v2.json','metadata-after.js','metadata-after.json','metadata-after.stdout','metadata-after.stderr']))
 server=r['server'];tree_hash=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
 result={'passed':True,'actual_Synchronet_audio_accepted':True,'cohort':str(out.relative_to(ROOT)),'route':'login/stock-XMODEM-CRC-upload/post-transfer-Files/Main',
  'check_counts':{'producer':len(r['checks']),'independent':len(base['checks']),'ownership':len(io['checks']),'official_metadata':len(metadata['checks']),'control_timing':len(timing['checks'])},'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],'metadata_checks':metadata['checks'],'control_timing_checks':timing['checks'],'control_timing_inputs':timing['inputs'],'metadata':metadata['metadata'],'original_metadata_audit_sha256':metadata['original_audit_sha256'],'source_authority':metadata['source_authority'],'startup_requests':metadata['startup_requests'],'startup_timeouts':metadata['startup_timeouts'],'data_block_errors':metadata['data_block_errors'],'upload':r['upload'],'protocol':base['protocol'],
  'terminal_sha256':sha(out/'program/TERMINAL.EXE'),'ASPECT_sha256':sha(out/'program/ASPECT.EXE'),'observed_hold_ms':int(holds[0][0]),'exact_online_bytes':len(online),'exact_BBS_display_bytes':len(display),
  'payloads':base['payloads'],'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],'script_stages':r['script_stages'],
  'server_source_commit':server['source_commit'],'official_server_binary_sha256':server['binary_sha256'],'server_archives':server['archives'],
  'immutable_server_file_count':len(server['server_inputs']),'server_input_tree_sha256':tree_hash(server['server_inputs']),'loaded_library_sha256':server['server_libraries'],
  'statistics_before':r['statistics_before'],'statistics_after':r['statistics_after'],'prerequisite_inputs':prerequisites,'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],
  'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'One actual source-built DOS/ASPECT stock Synchronet/sexyz XMODEM-1K/CRC upload through real SIP/RTP/V22-1200 audio at38400DTE. Unique11521-byte source plus127SUB padding in14 integrity-checked blocks, native controls/two-EOT finish, official full successful receive/log/metadata with3 attributable startup no-input timeouts and zero data-block errors, post-transfer Files/Main and normal DOS/UART/IRQ/PIC/timer/SIP cleanup. Explicit monotonic-hold/key-framing runtime; code/config/library/messages, all existing files and source identity preserved, no message/mail/download writes. Stock partial publication remains a separate known gap. Not other protocols, sustained pressure/carrier-loss/reconnect, physical Boca/SPA2102 or F01-F16 whole-application acceptance.'}

 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'actual_Synchronet_audio_accepted':True,'check_counts':result['check_counts'],'online_bytes':len(online),'display_bytes':len(display),'receipt':str(target)}))

if __name__=='__main__':main()
