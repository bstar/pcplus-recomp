#!/usr/bin/env python3
"""Audit exclusive WHEN key ownership during the real DOS ALARM/UART suite."""
import json,re,sys
from pathlib import Path
from build_context_help import ROOT,sha
import test_alarm_dos_uart as uart

def main():
 uart.main()
 out=Path(sys.argv[sys.argv.index('--output')+1]).resolve()
 report=json.loads((out/'result.json').read_text());assert report['passed']
 rows=[]
 for case in report['cases']:
  file=out/case['case']/'WHEN.TXT'
  match=re.fullmatch(r'WHEN ([01]) (\d+) (\d+) (\d+)\s*',file.read_text());assert match,case['case']
  attached,polls,leads,burst=map(int,match.groups())
  assert attached==int(case['case'].endswith('-E')) and polls>=case['callbacks']>0
  assert 0<leads<=508 and 0<burst<=64 if attached else leads==burst==0
  assert sha(file)==case['captures'][str(file.relative_to(out))]
  rows.append(dict(case=case['case'],modeled_attached=bool(attached),native_service_polls=polls,modeled_receive_leads=leads,max_receive_burst=burst))
 sources={**report['inputs'],'standalone/test_alarm_when_uart.py':sha(Path(__file__))}
 result=dict(passed=True,full_matrix=report['full_matrix'],binary_sha256=report['binary_sha256'],sources=sources,cases=rows,UART_result_sha256=sha(out/'result.json'),original_inputs=[],scope=__doc__+' Actual WHEN C key/transport/foreground gates and real UART/PIT/BIOS platform. Native WHEN action bodies and receive/renderer entry are modeled; no VM, parent PRM, original translation/action/parser or physical acceptance. Raw bytes remain queued at the WHEN gate; enhanced-mode cases exercise a modeled attached receive entry with real UART reads. Key lease survives speaker quarantine until explicit recovery.')
 (out/'when-result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS WHEN key lease:',len(rows),'real-I/O cases')
if __name__=='__main__':main()
