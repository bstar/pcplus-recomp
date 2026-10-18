#!/usr/bin/env python3
"""Record a matched DOS/stock-Synchronet SOFT/HARD Ctrl-Q comparison."""
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--soft',required=True);parser.add_argument('--hard',required=True);args=parser.parse_args()
 runs={}
 for kind,label in [('software',args.soft),('hardware',args.hard)]:
  assert label and all(c.isalnum() or c in '-_' for c in label)
  folder=ROOT/'build/bbs-lab/results/synchronet'/label
  experiment=read(folder/'experiment.json');run=read(folder/'result.json');audit=read(folder/'semantic-audit.json');modem=read(folder/'modem.json')
  assert experiment['binary_sha256']==run['binary_sha256']==audit['binary_sha256']
  assert experiment['source_sha256']=={s:sha(ROOT/s) for s in experiment['source_sha256']}
  assert run['passed'] and audit['checks']['stock_editor_entered']
  assert experiment['checks']==audit['checks'] and experiment['observed_key_wire']==audit['observed_key_wire']
  assert all(audit['observed_key_wire'].values()) and run['modem_packet_delay_ms']==0
  assert run['serial']==audit['serial']==experiment['serial']
  fixture=(folder/'TEST.PRM').read_bytes();assert len(fixture)==1264
  assert sha(folder/'TEST.PRM')==run['configuration']['sha256']
  assert modem['flow_mode']==('software' if kind=='software' else 'none')
  assert modem['baud']==run['serial']['baud'] and modem['packet_delay_ms']==0
  assert struct.unpack_from('<HH',fixture,0x198)==((1,0) if kind=='software' else (0,1))
  normalized=bytearray(fixture);normalized[0x198:0x19c]=bytes(4)
  runs[kind]=dict(label=label,experiment=experiment,run=run,semantic_evidence=audit,
   normalized_configuration_sha256=hashlib.sha256(normalized).hexdigest(),
   raw_serial_CtrlQ_count=(folder/'serial-received.bin').read_bytes().count(b'\x11'),
   BBS_wire_CtrlQ_count=(folder/'bbs-sent.bin').read_bytes().count(b'\x11'),
   observed_XON_events=[e for e in modem['events'] if e['kind']=='serial-flow' and e['value']==17],
   abort_after_editor_entry=(folder/'display.bin').read_bytes().find(b'Aborted.')>(folder/'display.bin').read_bytes().find(b'FSEditor v1.105')>=0,
   retained_artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(folder.iterdir()) if p.is_file()})
 soft,hard=runs['software'],runs['hardware']
 assert soft['experiment']['source_sha256']==hard['experiment']['source_sha256']
 assert soft['experiment']['binary_sha256']==hard['experiment']['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
 serials=[{k:v for k,v in entry['run']['serial'].items() if k!='flow'} for entry in [soft,hard]]
 assert serials[0]==serials[1] and serials[0]['com']==2 and serials[0]['baud']==19200 and serials[0]['line']=='8N1'
 assert soft['run']['serial']['flow']=='SOFT' and hard['run']['serial']['flow']=='HARD'
 assert soft['normalized_configuration_sha256']==hard['normalized_configuration_sha256']
 for key in ['keyboard','keyboard_input']:assert soft['run'][key]==hard['run'][key]
 for key in ['automatic_dial','mode','command','directory_entry','directory_browser','directory_sha256']:
  assert soft['run']['configuration'][key]==hard['run']['configuration'][key]
 checks=dict(same_binary_recipe_sources_COM_baud_line_and_PRM_except_flow=True,
  both_reached_stock_editor_and_emitted_all_eight_keys=True,
  software_only_fails_draft_abort=not soft['semantic_evidence']['checks']['draft_aborted'] and all(v for k,v in soft['semantic_evidence']['checks'].items() if k!='draft_aborted'),
  software_CtrlQ_emitted_but_consumed_as_XON=soft['raw_serial_CtrlQ_count']==1 and soft['BBS_wire_CtrlQ_count']==0 and len(soft['observed_XON_events'])==1,
  hardware_CtrlQ_reaches_BBS_and_aborts=hard['raw_serial_CtrlQ_count']==hard['BBS_wire_CtrlQ_count']==1 and hard['semantic_evidence']['passed'] and hard['semantic_evidence']['checks']['draft_aborted'] and hard['abort_after_editor_entry'])
 assert all(checks.values()),checks
 result=dict(recorded=True,binary_sha256=soft['experiment']['binary_sha256'],checks=checks,runs=runs,
  software_editor_passed=soft['semantic_evidence']['passed'],hardware_editor_passed=hard['semantic_evidence']['passed'],
  recorder_sha256=sha(Path(__file__)),
  scope='Matched actual DOS/owned stock Synchronet editor comparison: same COM2/19200/8N1, keyboard recipe, runtime, harness sources and PRM except its SOFT/HARD words. The modem model consumes Ctrl-Q as software XON; HARD delivers it and aborts. Server/user state is not reset between sequential runs; the recipe clears the synthetic body line. This establishes the modeled flow conflict, not physical modem firmware behavior or changing CTS timing.')
 target=ROOT/'docs/validation/bbs-synchronet-software-flow.json'
 if target.exists():
  previous=read(target);history=previous.pop('prior_experiments',[])
  old_labels={k:v['label'] for k,v in previous.get('runs',{}).items()}
  if old_labels!={k:v['label'] for k,v in runs.items()}:history.append(previous)
  if history:result['prior_experiments']=history
 target.write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded matched flow comparison: SOFT Ctrl-Q consumed; HARD editor abort passed')
if __name__=='__main__':main()
