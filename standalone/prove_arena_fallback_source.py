#!/usr/bin/env python3
"""Rebuild the compiler fix and replay allocation, grammar and nested DOS workflows."""
import argparse,ast,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from prove_reset_live_source import ROOT,FULL
from prove_native_bank_parent_source import SPECIAL_FLAGS
from check_compiler_arena_fallback import INPUTS
CHILD_FLAGS=['--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff','--custom-irq']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 products={'aspect-runner':'ASPECT.EXE','aspect-register-parent-custom-irq':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE',FULL:'TERMINAL.EXE'}
 sources={};expected={}
 def add(mapping):
  for name,digest in mapping.items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 for folder,leaf in products.items():
  m=load(ROOT/'build'/folder/'manifest.json');assert not m.get('original_inputs')and sha(ROOT/'build'/folder/leaf)==m['binary_sha256']
  expected[folder]=m['binary_sha256'];add(m['sources'])
 add({name:sha(ROOT/name)for name in INPUTS})
 pending=[Path(__file__),ROOT/'standalone/check_compiler_arena_fallback.py',ROOT/'standalone/check_aspect_compiler_stack.py',
  ROOT/'standalone/check_aspect_compiler_workspace.py',ROOT/'standalone/test_nested_compiler_memory_dos.py'];seen=set()
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
 for path in (ROOT/'standalone/fixtures').glob('aspect*.json'):sources[str(path.relative_to(ROOT))]=sha(path)
 for name in ['src/aspect/compiler.py','nix/flake.nix','nix/flake.lock','tools/dev']:sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('build','analysis','original','originals','install')
  assert path.suffix.lower()not in('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not(fresh/'build').exists()
 logs={};reports={}
 def run(label,argv,report=None):
  path=out/(label+'.log')
  with path.open('w')as log:subprocess.run([sys.executable,*argv],cwd=fresh,stdout=log,stderr=log,check=True,timeout=180)
  logs[label]=sha(path)
  if report:
   file=fresh/report;assert load(file)['passed'];reports[report]=sha(file)
 commands=[['standalone/build_aspect_runner.py'],['standalone/build_aspect_process.py',*CHILD_FLAGS],
  ['standalone/build_aspect_compiler_dos.py'],['standalone/build_terminal.py',*SPECIAL_FLAGS,'--native-reset-transaction']]
 for i,command in enumerate(commands):run('build-'+str(i),command)
 for folder,leaf in products.items():assert sha(fresh/'build'/folder/leaf)==expected[folder],folder
 assert expected['aspect-runner']=='bfd1a4e1998c8f82b27bdd35615948b3d94e8ae3bd308d03fb4187e728d3eed1'
 assert expected['aspect-register-parent-custom-irq']=='495d4852275bb7f14c897c8ea9fcaee4620c939690402898fd0c3c6e64723dd7'
 assert expected[FULL]=='64681b77eec3421a53647afdc1bde5c3fecc7025a1ed91f5376049cb4904997a'
 run('allocator',['standalone/check_compiler_arena_fallback.py','--output','build/allocator'],'build/allocator/checks.json')
 run('corpus-stack',['standalone/check_aspect_compiler_stack.py','--output','build/corpus-stack'],'build/corpus-stack/stack-checks.json')
 corpus=fresh/'build/corpus-stack/checks.json';assert load(corpus)['passed']and load(corpus)['case_count']==2043;reports[str(corpus.relative_to(fresh))]=sha(corpus)
 run('workspace',['standalone/check_aspect_compiler_workspace.py','--output','build/workspace'],'build/workspace/checks.json')
 for case,port,irq in [('explicit',2,5),('fallback',1,4),('chain',2,7),('rejected',1,5)]:
  report='build/nested/'+case+'/result.json'
  run(case,['standalone/test_nested_compiler_memory_dos.py','--output','build/nested/'+case,'--case',case,'--port',str(port),'--irq',str(irq),
   '--terminal','build/'+FULL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE',
   '--splash-key','--log-collisions','32'if case=='explicit'else'0'],report)
  assert all(load(fresh/report)['checks'].values())
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,source_files=len(sources),sources=sources,products=expected,commands=commands,reports=reports,logs=logs,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__,limitations=['No general low-memory guarantee or normal peer width/UI/BBS/physical acceptance.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS arena fallback source: four exact products, physical/logical allocation controls, full grammar/stack/workspace and four nested DOS cases')
if __name__=='__main__':main()
