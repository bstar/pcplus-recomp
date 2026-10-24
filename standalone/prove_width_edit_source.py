#!/usr/bin/env python3
"""Rebuild wide character editing and compiler size policy from declared sources."""
import argparse,ast,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from prove_native_bank_parent_source import ROOT,SPECIAL,SPECIAL_FLAGS
BASE='terminal-native-bank-transaction'
FULL=SPECIAL+'-transaction'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--nested',action='store_true');a=p.parse_args()
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
 children={'aspect-runner':'ASPECT.EXE','aspect-register-parent-custom-irq':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE'}if a.nested else{}
 child_hashes={}
 for folder,leaf in children.items():
  m=load(ROOT/'build'/folder/'manifest.json');child_hashes[folder]=sha(ROOT/'build'/folder/leaf);assert child_hashes[folder]==m['binary_sha256']
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 pending=[Path(__file__),ROOT/'standalone/check_reset_live.py',ROOT/'standalone/test_reset_live_dos.py',ROOT/'standalone/check_native_bank_parent.py',ROOT/'standalone/check_width_edit_live.py',ROOT/'standalone/check_character_edit_live.py'];seen=set()
 if a.nested:
  pending.extend(ROOT/'standalone'/name for name in ['test_nested_compiler_memory_dos.py','check_aspect_compiler_stack.py','check_aspect_compiler_workspace.py','check_compiler_arena_fallback.py'])
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
 if a.nested:
  from check_compiler_arena_fallback import INPUTS
  for name in INPUTS:sources[name]=sha(ROOT/name)
  for path in (ROOT/'src/aspect').glob('compiler_*.h'):sources[str(path.relative_to(ROOT))]=sha(path)
  sources['src/aspect/compiler.py']=sha(ROOT/'src/aspect/compiler.py')
  for path in (ROOT/'standalone/fixtures').glob('aspect*.json'):sources[str(path.relative_to(ROOT))]=sha(path)
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
   run('bank-'+folder,['standalone/check_native_bank_parent.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/native-bank-parent-checks.json')
   run('edits-'+folder,['standalone/check_width_edit_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/width-edit-checks.json')
   run('model-'+folder,['standalone/check_reset_live.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/reset-live-checks.json')
  elif not flags:run('characters80',['standalone/check_character_edit_live.py'],'build/terminal/character-edit-live-checks.json')
  elif flags:run('cold',['standalone/check_native_bank_parent.py','--terminal','build/'+folder+'/TERMINAL.EXE'],'build/'+folder+'/native-bank-parent-checks.json')
 assert expected['terminal']=='081457b0836fbf940aa41c12cf10cced9f02dec0ae5d60b34d15a3380d9ac75f'
 for folder,label in [(BASE,'base'),(FULL,'special')]:
  run('DOS-'+label,['standalone/test_reset_live_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/DOS-'+label,'--character-edits'],
   'build/DOS-'+label+'/checks.json')
  assert all(load(fresh/'build'/('DOS-'+label)/'checks.json')['checks'].values())
  run('DOS-hidden-'+label,['standalone/test_reset_live_dos.py','--terminal','build/'+folder+'/TERMINAL.EXE','--output','build/DOS-hidden-'+label,'--hidden-status','--character-edits'],
   'build/DOS-hidden-'+label+'/checks.json')
 if a.nested:
  run('build-default-runner',['standalone/build_aspect_runner.py'])
  run('build-runner',['standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff','--custom-irq'])
  run('build-compiler',['standalone/build_aspect_compiler_dos.py'])
  for folder,leaf in children.items():assert sha(fresh/'build'/folder/leaf)==child_hashes[folder],folder
  run('allocator',['standalone/check_compiler_arena_fallback.py','--output','build/allocator'],'build/allocator/checks.json')
  run('compiler-workspace',['standalone/check_aspect_compiler_workspace.py','--output','build/compiler-workspace'],'build/compiler-workspace/checks.json')
  run('compiler-stack',['standalone/check_aspect_compiler_stack.py','--output','build/compiler-stack'],'build/compiler-stack/stack-checks.json')
  corpus=load(fresh/'build/compiler-stack/checks.json');assert corpus['passed']and corpus['case_count']==2043
  reports['build/compiler-stack/checks.json']=sha(fresh/'build/compiler-stack/checks.json')
  for case,port,irq in [('explicit',2,5),('fallback',1,4),('chain',2,7),('rejected',1,5)]:
   report='build/nested/'+case+'/result.json'
   run('nested-'+case,['standalone/test_nested_compiler_memory_dos.py','--output','build/nested/'+case,'--case',case,'--port',str(port),'--irq',str(irq),
    '--terminal','build/'+FULL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE','--splash-key','--log-collisions','32'if case=='explicit'else'0'],report)
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,source_files=len(sources),sources=sources,products=expected,child_products=child_hashes,nested_compiler_verified=a.nested,reports=reports,logs=logs,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__,limitations=[
   'Plain wide character edits and explicit width API; normal peer width requests remain unbound.',
   'DOS witnesses call from real25-row startup, with default visible or fixture-hidden status; rollback/IRQ faults use the hardware model.',
   'Nested compiler trials use ordinary display; active-width child/UI composition remains open.'if a.nested else'Nested compiler admission is a separate gate and is not established by this proof.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS wide edits source: four exact products, two linked models and four DOS commits; nested compiler gate '+('passed'if a.nested else'separate'))
if __name__=='__main__':main()
