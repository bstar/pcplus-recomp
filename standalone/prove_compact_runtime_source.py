#!/usr/bin/env python3
"""Rebuild compact interpreters and repeat nested compilation from declared source only."""
import argparse,ast,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from prove_native_bank_parent_source import ROOT,SPECIAL,SPECIAL_FLAGS
CHILD_FLAGS=['--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff','--custom-irq']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 products={'aspect-runner':'ASPECT.EXE','aspect-register-parent-custom-irq':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE',SPECIAL:'TERMINAL.EXE'}
 sources={};expected={}
 for folder,leaf in products.items():
  m=load(ROOT/'build'/folder/'manifest.json');assert not m.get('original_inputs')and sha(ROOT/'build'/folder/leaf)==m['binary_sha256']
  expected[folder]=m['binary_sha256']
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 pending=[Path(__file__),ROOT/'standalone/check_compact_runtime_format.py',ROOT/'standalone/check_aspect_runner.py',ROOT/'standalone/check_aspect_source_compile.py',ROOT/'standalone/test_nested_compiler_memory_dos.py'];seen=set()
 while pending:
  path=pending.pop().resolve()
  if path in seen:continue
  seen.add(path);sources[str(path.relative_to(ROOT))]=sha(path)
  for node in ast.walk(ast.parse(path.read_text())):
   names=[x.name for x in node.names]if isinstance(node,ast.Import)else[node.module]if isinstance(node,ast.ImportFrom)else[]
   for name in names:
    if name:
     local=ROOT/'standalone'/(name.split('.')[0]+'.py')
     if local.is_file():pending.append(local)
 for name in ['src/aspect/compiler.py','nix/flake.nix','nix/flake.lock','tools/dev']:
  sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('build','analysis','original','originals','install')
  assert path.suffix.lower()not in('.exe','.obj','.img','.o','.prm','.dir','.xlt','.com')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not(fresh/'build').exists()
 logs={};reports={}
 def run(label,argv,report=None):
  log=out/(label+'.log')
  with log.open('w')as stream:subprocess.run([sys.executable,*argv],cwd=fresh,stdout=stream,stderr=stream,check=True,timeout=120)
  logs[label]=sha(log)
  if report:
   path=fresh/report;data=load(path);assert data['passed'];reports[report]=sha(path)
 commands=[['standalone/build_aspect_runner.py'],['standalone/build_aspect_process.py',*CHILD_FLAGS],
  ['standalone/build_aspect_compiler_dos.py'],['standalone/build_terminal.py',*SPECIAL_FLAGS]]
 for i,command in enumerate(commands):run('build-'+str(i),command)
 for folder,leaf in products.items():assert sha(fresh/'build'/folder/leaf)==expected[folder],folder
 assert expected['aspect-compiler-dos']=='18789792ad9e1be92057386d4405e4091e488d9bd8368490f414477e3dd5c8a2'
 assert expected[SPECIAL]=='dea8981a81c9d996b77cc8a9bed5166968b945bc9b5d9cbd9d2fce9ca579f17a'
 run('format',['standalone/check_compact_runtime_format.py','--output','build/format'],'build/format/checks.json')
 run('CLI',['standalone/check_aspect_runner.py'],'build/aspect-runner/checks.json')
 run('source-compile',['standalone/check_aspect_source_compile.py'],'build/aspect-source-compile/checks.json')
 for case,port,irq in [('explicit',2,5),('fallback',1,4),('chain',2,7),('rejected',1,5)]:
  report='build/nested/'+case+'/result.json'
  run(case,['standalone/test_nested_compiler_memory_dos.py','--output','build/nested/'+case,'--port',str(port),'--irq',str(irq),'--case',case,
   '--terminal','build/'+SPECIAL+'/TERMINAL.EXE','--runner','build/aspect-register-parent-custom-irq/ASPECT.EXE','--splash-key',
   '--log-collisions','32'if case=='explicit'else'0'],report)
  data=load(fresh/report);assert all(data['checks'].values())and data['products']['TERMINAL.EXE']==expected[SPECIAL]
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,products=expected,source_files=len(sources),sources=sources,commands=commands,reports=reports,logs=logs,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__,limitations=['No live width projection/transaction or BBS/physical hardware acceptance implied.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS compact runtime source: four exact products, CRT formatting, production CLI/source and four nested DOS cases')
if __name__=='__main__':main()
