#!/usr/bin/env python3
"""Bind GET lease wire matrix, clean export and GET-disabled ALARM comparison."""
import argparse,itertools,json
from pathlib import Path
from build_get_when_uart import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','matrix','cold','alarm','alarm-tests','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path,field=None):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');value=json.loads(path.read_text());assert value['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  if field:
   for name,digest in value[field].items():
    assert sha(ROOT/name)==digest
    if name in sources:assert sources[name]==digest
    sources[name]=digest
  return value
 m=load(a.build/'manifest.json','sources');u=load(a.matrix/'result.json','inputs');c=load(a.cold/'result.json','sources')
 binary=sha(a.build/'GETUART.EXE');assert binary==m['binary_sha256']==u['binary_sha256']==c['binary_sha256'] and m['original_inputs']==c['original_inputs']==[]
 expected={f'{port}-{flow}-{mode}-{keyboard}' for port,flow,mode,keyboard in itertools.product((1,2),'NSHB','AC','SE')}|{'1-N-F-S','1-S-F-E','2-H-F-S','2-B-F-E'}
 assert u['full_matrix'] and len(u['cases'])==len(expected)==36 and {r['case'] for r in u['cases']}==expected
 payload=bytes(n for n in range(256) if n not in (17,19))*2
 for row in u['cases']:
  assert row['passed'] and all(row['checks'].values()) and row['callbacks']>1
  attached=row['case'].endswith('-E');assert row['receive_leads']==(508 if attached else 0)
  assert 0<row['max_receive_burst']<=64 if attached else row['max_receive_burst']==0
  for name,digest in row['captures'].items():
   path=(a.matrix/name).resolve();assert path.is_relative_to(a.matrix.resolve()) and sha(path)==digest
  folder=a.matrix/row['case'];assert (folder/'RX.BIN').read_bytes()==payload
  assert (folder/'wire.bin').read_bytes()==(b'\x11RPF\x13' if row['case'].split('-')[1] in 'SB' else b'RPF')
 assert c['ancestor_git_unavailable'] and c['source_count']==23 and c['repeated_cases']==['1-N-A-S','2-S-C-E','1-S-F-E']
 repeated=a.cold/'source/build/tests/result.json';assert sha(repeated)==c['test_result_sha256'];repeat=load(repeated,'inputs')
 assert repeat['binary_sha256']==binary and [r['case'] for r in repeat['cases']]==c['repeated_cases']
 alarm=load(a.alarm/'manifest.json','sources');at=load(a.alarm_tests/'result.json','inputs');aw=load(a.alarm_tests/'when-result.json','sources');baseline=load(a.baseline/'result.json','sources')
 alarm_binary=sha(a.alarm/'ALARM.EXE');assert alarm_binary==alarm['binary_sha256']==at['binary_sha256']==aw['binary_sha256']==baseline['binary_sha256']
 assert [r['case'] for r in at['cases']]==[r['case'] for r in aw['cases']]==['1-N-N-S','2-S-K-E','1-N-G-S'] and all(r['passed'] for r in at['cases'])
 assert baseline['baseline_revision']=='f2fd97b' and baseline['current_manifest_sha256']==sha(a.alarm/'manifest.json')
 for name in ('standalone/prove_get_when_source.py','standalone/check_get_when_baseline.py','standalone/record_get_when.py','docs/ASPECT_GET_SERVICE.md'):sources[name]=sha(ROOT/name)
 summary=dict(DOS_cases=36,raw_cases=18,modeled_attached_cases=18,payload_per_case=508,cold_source_inputs=23,cold_wire_repeats=3,ALARM_regressions=3,observed_max_receive_burst=max(r['max_receive_burst'] for r in u['cases']))
 result=dict(checkpoint_verified=True,application_integrated=False,compiler_enabled=False,installed_changed=False,selector_changed=False,physical_verified=False,original_inputs=[],diagnostic_sha256=binary,GET_disabled_ALARM_sha256=alarm_binary,summary=summary,sources=sources,receipts=receipts,
  limitations=['Opt-in ASPECT_GET_SERVICE only; no opcode49/compiler, actual parent field/cursor protocol, native GET dispatcher or native abort unwind integration.',
   'Actual WHEN C key/admission/transport gates, source field, BIOS keyboard and UART ISR. Native WHEN action bodies and parent receive/parser entry are modeled; CALL/DISCONNECT/TRANSMIT and real carrier-loss handling during GET remain open.',
   'Raw/standard and modeled-attached/enhanced BIOS are two specific combinations. All508 bytes remain queued in raw mode or pass modeled receive entry in attached mode.',
   'Observed attached bursts are one lead;64-lead saturation is not tested. Nullmodem holds CTS ready and does not enforce RTS. Software XOFF/XON explicit; no physical modem/SIP/BBS or acoustic acceptance.',
   'Ordinary service errors permit explicit lease release; abandoned frames after nonlocal abort are not released by this API.',
   'Three ALARM wire regressions and exact GET-disabled pre-change WHEN source comparison; not a whole application rebuild or complete50-case ALARM matrix.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS GET lease receipt:',summary)

if __name__=='__main__':main()
