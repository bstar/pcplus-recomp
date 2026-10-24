#!/usr/bin/env python3
"""Reproduce live transaction parents and replay modeled/DOS ownership from source."""
import argparse,ast,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from prove_native_bank_parent_source import ROOT,SPECIAL,SPECIAL_FLAGS
BASE='terminal-native-bank-transaction'
FULL=SPECIAL+'-transaction'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 products=[('terminal',[]),('terminal-native-bank',['--native-reset-bank']),
  (BASE,['--native-reset-bank','--native-reset-transaction']),(FULL,SPECIAL_FLAGS+['--native-reset-transaction'])]
 sources={};expected={}
 for folder,flags in products:
  m=load(ROOT/'build'/folder/'manifest.json');assert sha(ROOT/'build'/folder/'TERMINAL.EXE')==m['binary_sha256']
  expected[folder]=m['binary_sha256']
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 pending=[Path(__file__),ROOT/'standalone/check_reset_live.py',ROOT/'standalone/test_reset_live_dos.py',ROOT/'standalone/check_native_bank_parent.py'];seen=set()
 while pending:
  path=pending.pop().resolve()
  if path in seen:continue
  seen.add(path);sources[str(path.relative_to(ROOT))]=sha(path)
  for node in ast.walk(ast.parse(path.read_text())):
   names=[item.name for item in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)else[]
   for name in names:
    if name:
     local=ROOT/'standalone'/(name.split('.')[0]+'.py')
     if local.is_file():pending.append(local)
 for name in ['standalone/line_attributes_watch.asm','nix/flake.nix','nix/flake.lock','tools/dev']:sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('build','analysis','original','originals','install')
  assert path.suffix.lower()not in('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not(fresh/'build').exists()
 logs={};reports={}
 def run(label,argv,report=None):
  log=out/(label+'.log')
  with log.open('w')as stream:subprocess.run([sys.executable,*argv],cwd=fresh,stdout=stream,stderr=stream,check=True,timeout=90)
  logs[label]=sha(log)
  if report:
   path=fresh/report;data=load(path);assert data['passed'];reports[report]=sha(path)
 for folder,flags in products:
  run('build-'+folder,['standalone/build_terminal.py',*flags])
  assert sha(fresh/'build'/folder/'TERMINAL.EXE')==expected[folder],folder
  if 'transaction'in folder:
   run('model-'+folder,['standalone/check_reset_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/reset-live-checks.json')
  elif flags:run('cold',['standalone/check_native_bank_parent.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/native-bank-parent-checks.json')
 assert expected['terminal']=='01f55dfbf5385136931c96700be3173cf8594be1c17677e9852fb0f1d025e447'
 assert expected['terminal-native-bank']=='999a9a329d88317f786ef2a22e7dd94c33bb2c994501b0a9d17cb2892ae74e52'
 for folder,label in [(BASE,'base'),(FULL,'special')]:
  run('DOS-'+label,['standalone/test_reset_live_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/DOS-'+label],
   'build/DOS-'+label+'/checks.json')
  assert all(load(fresh/'build'/('DOS-'+label)/'checks.json')['checks'].values())
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,source_files=len(sources),sources=sources,products=expected,reports=reports,logs=logs,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__,limitations=[
   'Plain24-row transaction only; normal peer width requests remain unbound.',
   'DOS witness stages admitted rows and calls at a BIOS boundary; rollback/IRQ faults use the hardware model.',
   'Nested compiler admission is a separate gate and is not established by this proof.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS live transaction source: four exact products, two linked models and two DOS commits; nested compiler gate separate')
if __name__=='__main__':main()
