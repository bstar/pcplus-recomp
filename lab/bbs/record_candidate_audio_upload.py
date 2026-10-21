#!/usr/bin/env python3
"""Seal a fully audited receiver-candidate audio upload at its exact scope."""
import argparse,hashlib,json
from pathlib import Path
from enigma_receive_finish_instance import ROOT,STOCK,from_result,validate
from enigma_upload_dos import metadata


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');context=from_result(r);assert context and r['route']=='upload' and not r.get('upload_cancel')
 base=read('independent-audit.json');io=read('serial-io-audit.json');upload=read('upload-audit.json')
 verifier=read('control-timing-verifier.json');finish=read('upload-finish-diagnosis.json')
 assert r['passed'] and base['passed'] and io['evidence_consistent'] and upload['passed']
 for d in (r,base,io,upload):assert all(d['checks'].values())
 assert verifier['passed'] and verifier['input_transfer_audit_passed'] and not verifier['protocol_only']
 assert len(verifier['negative_cases'])==2 and all(v['rejected'] for v in verifier['negative_cases'])
 assert not upload['errors'] and not upload['late_protocol_controls']
 assert finish['transfer_audit_passed'] and finish['sender_OO_frontend_after_helper_exit_ms']<=0
 assert all(v<=0 for v in finish['sender_OO_relay_after_helper_exit_ms'])
 for d in (r,upload,finish,verifier):
  hashes=d.get('captures_sha256',d.get('capture_sha256'))
  assert hashes and all(sha(out/n)==h for n,h in hashes.items())
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 for n,h in r['server_inputs'].items():assert sha(Path(context['source'])/n)==h,n
 commands=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(commands)
 online=serial[len(commands):];offline=bytes.fromhex(''.join(v['hex'] for v in read('offline-caller.json')['received']))
 assert online==offline and len(online)==base['payloads']['guest_DATA_RX_bytes']
 info=validate(ROOT/context['lab']);source=out/'SEND/AUDIOUP.BIN';stored=Path(r['upload']['prepared']['target_path'])
 assert len(source.read_bytes())==11521 and source.read_bytes()==stored.read_bytes()
 assert metadata(STOCK,['AUDIOUP.BIN'])==info['stock_upload']
 stock_file=STOCK/'file_base/pcplus_transfer/AUDIOUP.BIN'
 assert sha(stock_file)==info['stock_upload'][0]['entries'][0]['fileSha256']==sha(source)
 for n,h in info['stock_server_inputs'].items():assert sha(STOCK/n)==h,n
 assert sha(STOCK.parent/'helpers/sexyz')==info['stock_helper_sha256']
 assert sha(Path(info['helper']))==context['helper_sha256']
 keyboard=bytes.fromhex(finish['post_protocol_keyboard_hex']);search=b'S\rAUDIOUP.BIN\r\r'
 assert keyboard.endswith(search) and set(keyboard[:-len(search)])<={9,13} and len(keyboard[:-len(search)])<=16
 protocol=upload['protocol'];assert len(protocol['files'])==1 and protocol['files'][0]['length']==11521
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json',
  'upload-audit.json','upload-finish-diagnosis.json','control-timing-verifier.json','offline-caller.json']))
 result={'passed':True,'candidate_audio_accepted':True,'stock_audio_upload_accepted':False,
  'cohort':str(out.relative_to(ROOT)),'server_fixture':context,
  'checks':{'producer':True,'independent_byte_cleanup':True,'serial_ownership':True,
   'protocol_file_and_resume':True,'timing_verifier_negatives':True,
   'offline_caller_equals_complete_online_input':True,'closing_OO_precedes_helper_exit':True,
   'stock_server_helper_and_upload_preserved':True,'actual_post_transfer_search_keys':True},
  'check_counts':{'producer':len(r['checks']),'independent':len(base['checks']),
   'ownership':len(io['checks']),'protocol_file_resume':len(upload['checks'])},
  'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],'transfer_checks':upload['checks'],
  'terminal_sha256':r['frozen_inputs']['build/terminal/TERMINAL.EXE'],
  'map_sha256':r['frozen_inputs']['build/terminal/terminal.map'],
  'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],
  'server_revision':r['server_revision'],'server_inputs':r['server_inputs'],
  'payloads':base['payloads'],'source_file_bytes':11521,'source_and_installed_file_sha256':sha(source),
  'official_metadata':upload['official_metadata'],'protocol':protocol,
  'control_timing':upload['control_timing'],'timing_verifier':verifier,'finish_diagnosis':finish,
  'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],
  'post_transfer_keyboard_hex':keyboard.hex(),'gateway_errors':r['gateway']['errors'],
  'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'One full-size actual DOS upload on the explicitly isolated ENiGMA board using the pinned Nix receiver-finish candidate and unchanged V22/1200 framed SIP/RTP/DSP runtime at fixed38400 DTE. All recorded producer, exact byte/cleanup, ownership and CRC/control/storage/return/closing gates pass without waiver. Original source/stat and stock server/helper/upload remain preserved. This accepts only this modified-helper audio workflow; unmodified stock still has the recorded closing gap. Cancellation/loss/pressure, arbitrary other peers, physical Boca/SPA2102 and all F01-F16 requirements remain open.'}
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'candidate_audio_accepted':True,'stock_audio_upload_accepted':False,'check_counts':result['check_counts'],'receipt':str(target)}))


if __name__=='__main__':main()
