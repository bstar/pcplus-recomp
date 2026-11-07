#!/usr/bin/env python3
"""Bind real DOS ALARM key-lease I/O and cold reproduction evidence."""
import argparse,itertools,json
from pathlib import Path
from build_context_help import ROOT,sha
from test_alarm_dos_uart import PAYLOAD

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','matrix','cold','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();matrix=a.matrix.resolve();cold=a.cold.resolve();sources={};receipts={}
 def load(path,field=None):
  d=json.loads(path.read_text());assert d['passed'],path;receipts[str(path.relative_to(ROOT))]=sha(path)
  if field:
   for name,digest in d[field].items():
    assert sha(ROOT/name)==digest,name
    if name in sources:assert sources[name]==digest,name
    sources[name]=digest
  return d
 m=load(build/'manifest.json','sources');u=load(matrix/'result.json','inputs');w=load(matrix/'when-result.json','sources');c=load(cold/'result.json','sources')
 binary=sha(build/'ALARM.EXE');assert binary==m['binary_sha256']==u['binary_sha256']==w['binary_sha256']==c['binary_sha256']
 assert m['diagnostic_build'] and m['original_inputs']==c['original_inputs']==[] and m['main_bank']!=m['speaker_bank']
 assert u['full_matrix'] and w['full_matrix'] and sha(matrix/'result.json')==w['UART_result_sha256']
 expected={f'{port}-{flow}-{mode}-S' for port,flow,mode in itertools.product((1,2),'NSHB','NQKFB')}
 expected|={f'{port}-{flow}-K-E' for port,flow in itertools.product((1,2),'NSHB')}
 expected|={'1-N-G-S','2-S-G-E'}
 assert len(u['cases'])==len(w['cases'])==len(expected)==50
 assert {r['case'] for r in u['cases']}=={r['case'] for r in w['cases']}==expected
 for row,owner in zip(u['cases'],w['cases']):
  label=row['case'];assert label==owner['case'] and row['passed'] and all(row['checks'].values())
  assert row['callbacks']>1 and owner['native_service_polls']>=row['callbacks']
  attached=label.endswith('-E');assert owner['modeled_attached']==attached
  if attached:assert 0<owner['modeled_receive_leads']<=508 and 0<owner['max_receive_burst']<=64
  else:assert owner['modeled_receive_leads']==owner['max_receive_burst']==0
  for name,digest in row['captures'].items():
   path=matrix/name;assert path.resolve().is_relative_to(matrix) and sha(path)==digest,name
  assert (matrix/label/'RX.BIN').read_bytes()==PAYLOAD
  assert (matrix/label/'wire.bin').read_bytes()==(b'\x11RPF\x13' if label.split('-')[1] in 'SB' else b'RPF')
 assert c['source_files']==len(c['sources'])==35 and c['cases']==['1-N-N-S','2-S-K-E','1-N-G-S']
 repeat=cold/'source/build/tests/when-result.json';assert sha(repeat)==c['test_result_sha256']
 repeated=json.loads(repeat.read_text());assert repeated['passed'] and repeated['binary_sha256']==binary
 assert [r['case'] for r in repeated['cases']]==c['cases']
 default=sha(ROOT/'build/aspect-runner/ASPECT.EXE');assert default=='91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
 sources['standalone/record_alarm_when.py']=sha(Path(__file__))
 summary=dict(DOS_cases=50,UART_payload_per_case=508,raw_gate_cases=sum(not r['modeled_attached'] for r in w['cases']),modeled_receive_cases=sum(r['modeled_attached'] for r in w['cases']),cold_source_files=35,cold_repeated_cases=3)
 report=dict(passed=True,sources=sources,receipts=receipts,binary_sha256=binary,default_interpreter_sha256=default,summary=summary,
  limitations=['Opt-in ASPECT_ALARM_SERVICE ownership path; no ALARM opcode/VM, parent sound/duration policy or shipping package binding.',
   'Actual WHEN C admission, key-ready, transport and foreground polling execute. Native WHEN action bodies and receive/renderer entry are modeled; no original translation, WHEN CALL/TRANSMIT/DISCONNECT or parent parser acceptance.',
   'Actual DOS clock, BIOS keys, banked PIT and UART operate in muted8086 emulator. No acoustic, physical modem/SIP/BBS acceptance. Nullmodem CTS stays ready and RTS is not enforced.',
   'Raw gate keeps incoming bytes queued for the diagnostic consumer. Modeled attached receive entry reads real UART bytes; existing diagnostic consumer can also read. This does not establish all508 bytes passed through a real renderer.',
   'Cold rebuild repeats three selected cases, not the full50 matrix. Default interpreter binary unchanged; no selected package or installed files changed.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS ALARM WHEN key lease',summary)
if __name__=='__main__':main()
