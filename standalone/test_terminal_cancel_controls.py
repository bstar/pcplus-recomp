#!/usr/bin/env python3
"""Run existing actual-DOS prompt/deferred-answer checks on the guarded client."""
import argparse,contextlib,json,re,shutil,sys
from pathlib import Path
import test_setup_startup_dos as setup
import test_translation_reload_dos as reload
from build_aspect_process import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--mouse',action='store_true')
 a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
 out=ROOT/'build/terminal-cancel-controls'/a.label;out.mkdir(parents=True,exist_ok=False)
 binary=ROOT/'build'/('terminal-traps-mouse' if a.mouse else 'terminal-traps')/'TERMINAL.EXE'
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['terminal_traps']
 assert manifest['binary_sha256']==sha(binary)
 names=['test_terminal_cancel_controls.py','test_translation_reload_dos.py','test_setup_startup_dos.py',
  'check_setup_model.py','check_directory_live.py','test_terminal.py']
 sources={**manifest['sources'],**{'standalone/'+n:sha(ROOT/'standalone'/n) for n in names}}
 for n,h in sources.items():
  assert sha(ROOT/n)==h,n
  target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 setup.BINARY=reload.BINARY=binary;setup.OUT=reload.OUT=out/'dos';cases=[]
 for kind in ['accept','decline','early-answer']:
  label=a.label+'-'+kind
  sys.argv=['test_translation_reload_dos.py','--label',label,'--sha256',sha(binary),'--case',kind]
  with (out/(kind+'.log')).open('w') as log,contextlib.redirect_stdout(log):reload.main()
  path=ROOT/'build/translation-reload-dos'/label/'checks.json'
  receipt=json.loads(path.read_text());assert receipt['passed'] and receipt['binary_sha256']==sha(binary)
  assert len(receipt['cases'])==1 and all(receipt['cases'][0]['checks'].values())
  cases.append(dict(kind=kind,receipt=str(path.relative_to(ROOT)),sha256=sha(path),checks=receipt['cases'][0]['checks']))
  print(kind,'PROMPT CONTROL PASS',flush=True)
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,mouse=a.mouse,binary_sha256=sha(binary),sources=sources,cases=cases,
  scope='Existing actual DOS PROGRAM/file mutation, accepted/declined table reload and queued early Y answer. Explicit adapter changes only binary/output/CLI selection. No event injection or physical modem claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
