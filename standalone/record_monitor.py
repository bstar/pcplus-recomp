#!/usr/bin/env python3
"""Publish monitor evidence with explicit native, linked, DOS and history scopes."""
import argparse,hashlib,json
from pathlib import Path
from test_terminal_monitor_dos import recipes
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def write(name,data):(ROOT/'docs/validation'/name).write_text(json.dumps(data,indent=2)+'\n')
def sources(d):
 for p,h in d['sources'].items():assert sha(p)==h,p

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dos-label',action='append',required=True);a=p.parse_args()
 runtime=sha('build/terminal/TERMINAL.EXE')
 manifest=read('build/monitor/manifest.json');native=read('build/monitor/checks.json');native_dos=read('build/monitor-dos/result.json')
 assert native['passed'] and native_dos['passed'] and manifest['binary_sha256']==native['binary_sha256']==native_dos['binary_sha256']==sha('build/monitor/MONITOR.EXE')
 sources(manifest)
 write('monitor-native.json',dict(native,manifest=manifest,provenance=read('reconstruction/monitor/provenance.json')))
 write('monitor-native-dos.json',native_dos)
 owner=read('build/monitor-file/result.json');assert owner['passed'];sources(owner)
 for name,h in owner['binaries'].items():assert sha('build/monitor-file/'+name)==h,name
 write('monitor-file.json',owner)
 linked=read('build/terminal/terminal-monitor-live-checks.json');assert linked['passed'] and linked['binary_sha256']==runtime
 linked['test_source_sha256']=sha('standalone/check_terminal_monitor_live.py')
 linked['retained_fixture_failures']=[{'path':str(f.relative_to(ROOT)),'sha256':sha(f.relative_to(ROOT))} for f in sorted((ROOT/'build/terminal-monitor-linked').glob('initial-9d90-*'))]
 linked['history_notes']='Initial hardware model lacked BIOS AH06; two later driver-only errors used a shadowed helper name and a private linker symbol. Product code was unchanged while the fixture was corrected; retained logs are separate from the passing current test.'
 write('terminal-monitor-live.json',linked)
 history=[];latest={}
 for label in a.dos_label:
  assert label and all(c.isalnum() or c in '-_' for c in label)
  batch=read('build/terminal-monitor-dos/'+label+'/checks.json')
  for case in batch['cases']:
   folder=ROOT/'build/terminal-monitor-dos'/label/case['case']
   assert case==json.loads((folder/'result.json').read_text())
   record=dict(case,label=label,retained_artifacts={str(q.relative_to(ROOT)):sha(q.relative_to(ROOT)) for q in sorted(folder.iterdir()) if q.is_file()})
   history.append(record);latest[case['case']]=dict(label=label,passed=case['passed'],binary_sha256=case['binary_sha256'])
 assert set(latest)=={r['name'] for r in recipes()}
 assert all(r['passed'] and r['binary_sha256']==runtime for r in latest.values())
 write('terminal-monitor-dos.json',dict(binary_sha256=runtime,runs=history,latest_selected_cases=latest,latest_selected_cases_passed=True,all_recorded_cases_passed=all(r['passed'] for r in history),harness_source_sha256=sha('standalone/test_terminal_monitor_dos.py'),history_notes='Initial explicit PRM case failed an independent attribute oracle expecting default0F; the fixture explicitly configures2F and the runtime displayed2F. Its failed result is retained. A fresh corrected PRM-only rerun passes; no product executable change.',scope='Actual DOS UART/monitor/render/file-owner/keyboard tests on synthetic media with independent B800 and kernel-write observers. Current selected15 cases pass; history is retained separately. No physical hardware, general software-flow all-byte, disk-fault injection or complete original UI/HOOK claim.'))
 print('Recorded monitor',runtime,len(latest),'selected actualDOS cases;',len(history),'historical runs')
if __name__=='__main__':main()
