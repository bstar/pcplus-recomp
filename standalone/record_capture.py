#!/usr/bin/env python3
"""Record explicitly selected capture evidence, retaining failures and retries."""
import argparse,hashlib,json
from pathlib import Path
from test_terminal_capture_dos import recipes
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def save(name,value):
 (ROOT/'docs/validation'/name).write_text(json.dumps(value,indent=2)+'\n')
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--dos-label',action='append',required=True,help='Chronological labels; later retry selects its own case only')
 args=parser.parse_args();runtime=digest(ROOT/'build/terminal/TERMINAL.EXE')
 for folder,name in [('capture-file','capture-file.json'),('capture-session','capture-session.json')]:
  report=read(ROOT/'build'/folder/'result.json');assert report['passed'],folder
  for source,expected in report['sources'].items():assert digest(ROOT/source)==expected,source
  for binary,expected in report['binaries'].items():assert digest(ROOT/'build'/folder/binary)==expected,binary
  save(name,report)
 linked=read(ROOT/'build/terminal/terminal-capture-live-checks.json')
 assert linked['passed'] and linked['binary_sha256']==runtime
 save('terminal-capture-live.json',linked)
 history=[];selected={}
 for label in args.dos_label:
  assert label.replace('-','').replace('_','').isalnum(),label
  base=ROOT/'build/terminal-capture-dos'/label;batch=read(base/'checks.json')
  for case in batch['cases']:
   folder=base/case['case'];result=read(folder/'result.json');assert case==result
   record={k:result[k] for k in ['case','passed','checks','errors','binary_sha256','seconds','command','keys','scope']}
   record['label']=label
   record['retained_artifacts']={str(p.relative_to(ROOT)):digest(p) for p in sorted(folder.iterdir()) if p.is_file()}
   if (folder/'kernel-trace.json').is_file():record['kernel_trace']=read(folder/'kernel-trace.json')
   if 'observations' in result:record['observations']=result['observations']
   history.append(record);selected[case['case']]={'label':label,'passed':result['passed'],'binary_sha256':result['binary_sha256']}
 assert set(selected)=={r['name'] for r in recipes()},'Incomplete case selection'
 assert all(r['binary_sha256']==runtime for r in selected.values()),'Selected case uses an earlier runtime'
 save('terminal-capture-dos.json',{
  'binary_sha256':runtime,'runs':history,'latest_selected_cases':selected,
  'latest_selected_cases_passed':all(r['passed'] for r in selected.values()),
  'all_recorded_cases_passed':all(r['passed'] for r in history),
  'harness_source_sha256':digest(ROOT/'standalone/test_terminal_capture_dos.py'),
  'history_notes':[
   'initial-132f readonly denial acquired no handle but caused exit12; fixed owner-aware shutdown in current runtime.',
   'Initial host periodic file visibility was an invalid write-timing oracle; actual DOS calls are now independently traced.',
   'final-6b69 periodic tracing proved early write but a false DOS shell redirect created an empty error marker; corrected harness retry preserves the same runtime.',
  ],
  'scope':'Actual DOS text-capture UI/UART/files/hardware snapshots; synthetic owned media. Trace proves an early DOS write, not host visibility, exact18tick timing or durability. Historical failures remain distinct from selected retries. Physical modem, raw monitoring, snapshots, printer and ASPECT remain unvalidated.'})
 print('Recorded capture evidence:',runtime,len(selected),'selected cases;',sum(not r['passed'] for r in history),'historical failures retained')
if __name__=='__main__':main()
