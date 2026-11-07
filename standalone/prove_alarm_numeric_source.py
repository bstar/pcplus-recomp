#!/usr/bin/env python3
"""Cold public-source rebuild of the numeric-bank ALARM parent/child variant."""
import argparse,hashlib,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent','child','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False);fresh=out/'source';fresh.mkdir();sources={}
 expected={}
 for folder,binary in ((a.parent.resolve(),'TERMINAL.EXE'),(a.child.resolve(),'ASPECT.EXE')):
  manifest=json.loads((folder/'manifest.json').read_text());expected[binary]=sha(folder/binary);assert manifest['binary_sha256']==expected[binary]
  for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
 extra=['standalone/prove_alarm_numeric_source.py','standalone/test_aspect_alarm_vm_dos.py','standalone/test_numeric_banks_dos.py','standalone/numeric_bank_diagnostic.c','standalone/test_numeric_bank_vm_dos.py','standalone/chat_redisplay_profile.json','standalone/test_alarm_cooperative_dos.py','standalone/test_alarm_progress_dos.py','standalone/alarm_speaker_observer.py','standalone/alarm_error_fixtures.py']
 for name in extra:sources[name]=sha(ROOT/name)
 base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',base_commit],cwd=ROOT)))as tar:
  tar.extractall(fresh,members=[m for m in tar.getmembers()if m.name.split('/')[0]not in ('analysis','build','.git')],filter='data')
 for name,digest in sources.items():
  assert Path(name).parts[0]not in ('analysis','build','.git')
  target=fresh/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 assert not any((fresh/name).exists()for name in ('analysis','build','.git'))
 inventory={str(f.relative_to(fresh)):sha(f)for f in fresh.rglob('*')if f.is_file()}
 parent=fresh/'build/terminal-alarm-policy-admission-20261106';child=fresh/'build/aspect-alarm-vm-numeric-final-20261106'
 with(out/'build.log').open('w')as log:
  def run(args):subprocess.run([sys.executable,*args],cwd=fresh,stdout=log,stderr=log,check=True)
  flags=json.loads((fresh/'standalone/chat_redisplay_profile.json').read_text())
  run(['standalone/build_terminal.py','--output-dir',str(parent),*flags,'--global-help','--chat-help','--aspect-alarm-policy'])
  code='from pathlib import Path;import sys;sys.path.insert(0,"standalone");from build_aspect_process import main;main(parent_render=True,output=Path.cwd()/"build/aspect-alarm-vm-numeric-final-20261106",notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,snapshot_lease=True,defer_script_buffers=True,alarm_vm=True)'
  run(['-c',code]);actual={'TERMINAL.EXE':sha(parent/'TERMINAL.EXE'),'ASPECT.EXE':sha(child/'ASPECT.EXE')};assert actual==expected,(actual,expected)
  run(['standalone/test_numeric_banks_dos.py','--output',str(fresh/'build/unit')])
  run(['standalone/test_alarm_cooperative_dos.py','--output',str(fresh/'build/legacy')])
  run(['standalone/test_alarm_progress_dos.py','--output',str(fresh/'build/progress')])
  for name,flags in [('numeric',[]),('strings',['--strings'])]:run(['standalone/test_numeric_bank_vm_dos.py','--runner',str(child/'ASPECT.EXE'),'--output',str(fresh/'build'/name),*flags])
  run(['standalone/test_aspect_alarm_vm_dos.py','--label','cold-plain','--terminal-sha256',actual['TERMINAL.EXE'],'--runner-sha256',actual['ASPECT.EXE'],'--case','alarm-vm-plain-terminal'])
 results={}
 for name,path in [('unit',fresh/'build/unit/result.json'),('legacy',fresh/'build/legacy/result.json'),('progress',fresh/'build/progress/result.json'),('numeric',fresh/'build/numeric/result.json'),('strings',fresh/'build/strings/result.json'),('ALARM',fresh/'build/aspect-alarm-vm-dos/cold-plain/pause-checks.json')]:
  r=json.loads(path.read_text());assert r['passed'],name;count=r.get('cases',r.get('checks'));results[name]=dict(sha256=sha(path),cases=count if isinstance(count,int) else len(count),deep_cases=len(r.get('deep_cases',[])))
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 (out/'inventory.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n')
 report=dict(passed=True,products=actual,source_files=len(inventory),source_base_commit=base_commit,inventory_sha256=sha(out/'inventory.json'),overlay_sources=sources,results=results,original_inputs=[],scope=__doc__+' Public HEAD plus declared source overlay; no original binary, private files, prior objects or Git metadata. Exact products; full bank API, legacy/progress modeled clock suites and512+512 native VM cases, then one actual parent/ALARM/render case with UMB observer. Does not repeat native WHEN matrix, full parent capacity/BBS or physical acceptance. Pinned toolchain supplied by caller.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cold numeric ALARM:',len(inventory),'sources')
if __name__=='__main__':main()
