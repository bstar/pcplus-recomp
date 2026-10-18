#!/usr/bin/env python3
"""Publish explicit snapshot checkpoints with runtime identities and history."""
import argparse,hashlib,json
from pathlib import Path
from test_terminal_snapshot_dos import recipes
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(name,data):(ROOT/'docs/validation'/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--dos-label',action='append',required=True);a=p.parse_args()
 runtime=digest(ROOT/'build/terminal/TERMINAL.EXE')
 native=read(ROOT/'build/snapshot/checks.json');manifest=read(ROOT/'build/snapshot/manifest.json')
 assert native['passed'] and native['binary_sha256']==manifest['binary_sha256']==digest(ROOT/'build/snapshot/SNAPSHOT.EXE')
 for source,expected in manifest['sources'].items():assert digest(ROOT/source)==expected,source
 write('snapshot-native.json',dict(native,manifest=manifest))
 dos=read(ROOT/'build/snapshot-dos/result.json');assert dos['passed'] and dos['binary_sha256']==native['binary_sha256'];write('snapshot-native-dos.json',dos)
 owners=read(ROOT/'build/capture-owners/result.json');assert owners['passed']
 for source,expected in owners['sources'].items():assert digest(ROOT/source)==expected,source
 for binary,expected in owners['binaries'].items():assert digest(ROOT/'build/capture-owners'/binary)==expected,binary
 write('capture-owners.json',owners)
 for source,target in [('build/terminal/terminal-snapshot-live-checks.json','terminal-snapshot-live.json'),('build/far-storage/linked-checks.json','snapshot-far-linked.json'),('build/far-storage-dos/checks.json','snapshot-far-dos.json')]:
  report=read(ROOT/source);assert report['passed'] and report['binary_sha256']==runtime,source;write(target,report)
 history=[];latest={}
 for label in a.dos_label:
  assert label.replace('-','').replace('_','').isalnum()
  base=ROOT/'build/terminal-snapshot-dos'/label;batch=read(base/'checks.json')
  for case in batch['cases']:
   folder=base/case['case'];assert case==read(folder/'result.json')
   record=dict(case,label=label,retained_artifacts={str(f.relative_to(ROOT)):digest(f) for f in sorted(folder.iterdir()) if f.is_file()})
   history.append(record);latest[case['case']]=dict(label=label,passed=case['passed'],binary_sha256=case['binary_sha256'])
 assert set(latest)=={r['name'] for r in recipes()}
 assert all(r['binary_sha256']==runtime for r in latest.values())
 write('terminal-snapshot-dos.json',dict(binary_sha256=runtime,runs=history,latest_selected_cases=latest,
  latest_selected_cases_passed=all(r['passed'] for r in latest.values()),all_recorded_DOS_cases_passed=all(r['passed'] for r in history),
  harness_source_sha256=digest(ROOT/'standalone/test_terminal_snapshot_dos.py'),
  linked_prior_failure=dict(binary_sha256='07d937f514ca48c65f06acf64b21ef1d90e6eb14df660b023c624e2e7174ef01',passed=False,
   operation='terminal_snapshot_start',configured_CGA_port=0x3da,modeled_retrace_input=0,instruction_limit=3000000,
   observation='Rejected CGA setting reached the denial notice ui_read_byte retrace wait and did not return; IN/CLI loop observed at ui_read_byte+39.',
   corrected='Current unsupported-CGA path records denied and skips that renderer; linked tests verify bounded return, no fileIO and interrupts enabled.'),
  history_notes=['07d9 original11 and strengthened4 DOS cases pass; current runtime repeats all11 strengthened cases.','The prior unsupported-CGA failure is a separate linked hardware model observation, not an actual DOS/CGA hardware result.'],
  scope='Actual DOS Alt-G/UART/files with independent25-row oracle, BIOS cursor/mode/page and hardware snapshots. Previous runtimes and verifier-strengthening runs stay separate. NUL/SUB/shadow, write faults and unsupported CGA use separate native/linked evidence. No physical hardware claim.'))
 print('Recorded snapshot:',runtime,len(latest),'selected cases;',len(history),'DOS runs retained')
if __name__=='__main__':main()
