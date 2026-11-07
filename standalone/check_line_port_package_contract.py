#!/usr/bin/env python3
"""Exercise matched Line/Port or Meta companion admission and public archives."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha,terminal_companions


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','package','recipe','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--module',choices=['line','meta'],default='line')
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 terminal=a.terminal.resolve();package=a.package.resolve();recipe=a.recipe.resolve()
 assert terminal.is_relative_to(ROOT/'build') and package.is_relative_to(ROOT/'build') and recipe.is_relative_to(ROOT)
 original=json.loads(terminal.with_name('manifest.json').read_text());assert sha(terminal)==original['binary_sha256']
 meta=a.module=='meta';leaf='PCMETA.OVL' if meta else 'PCLINE.OVL'
 descriptor='meta_editor_overlay' if meta else 'line_port_overlay'
 feature='experimental_meta_editor_module' if meta else 'experimental_line_port_overlay'
 native='experimental_meta_editor' if meta else 'experimental_line_port'
 layout='meta_loader_retained' if meta else 'line_port_overlay_contract_verified'
 fixture=out/'product';fixture.mkdir()
 for name in ('TERMINAL.EXE','PCLINE.OVL','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP','package.json'):
  shutil.copyfile(terminal.with_name(name),fixture/name)
 if meta:
  for name in ('PCMETA.OVL','terminal.map'):shutil.copyfile(terminal.with_name(name),fixture/name)
 blob=(fixture/leaf).read_bytes();cases=[]
 extra=('forged-hash','wrong-fixup-count','shared-layout-missing') if meta else ()
 for name in ('valid','missing','corrupt','flag-missing','descriptor-missing','native-missing','layout-missing','plain-control',*extra):
  m=json.loads(json.dumps(original));(fixture/leaf).write_bytes(blob)
  if name=='missing':(fixture/leaf).unlink()
  elif name in ('corrupt','forged-hash'):
   (fixture/leaf).write_bytes(bytes([blob[0]^1])+blob[1:])
   if name=='forged-hash':m[descriptor]['sha256']=sha(fixture/leaf)
  elif name=='flag-missing':m[feature]=False
  elif name=='descriptor-missing':del m[descriptor]
  elif name=='native-missing':m[native]=False
  elif name=='layout-missing':m['memory_layout'][layout]=False
  elif name=='wrong-fixup-count':m[descriptor]['relocations']+=1
  elif name=='shared-layout-missing':m['experimental_meta_shared_runtime']=False
  elif name=='plain-control':
   for key in ('line_port_overlay','experimental_line_port_overlay','experimental_line_port','experimental_global_help','experimental_chat_loader','meta_editor_overlay','experimental_meta_editor_module','experimental_meta_editor','experimental_meta_shared_runtime'):m.pop(key,None)
  try:files,_=terminal_companions(fixture/'TERMINAL.EXE',m);accepted=True
  except (AssertionError,FileNotFoundError):accepted=False
  assert accepted==(name in ('valid','plain-control')),name
  if name=='valid':assert files[leaf].read_bytes()==blob
  if name=='plain-control':assert files=={}
  cases.append(dict(case=name,accepted=accepted))
 for name in ('archive-missing','archive-corrupt','archive-undeclared'):
  copy=out/name;shutil.copytree(package,copy);m=json.loads((copy/'manifest.json').read_text())
  if name=='archive-missing':del m['files'][leaf]
  elif name=='archive-corrupt':(copy/m['dos_directory']/leaf).write_bytes(b'wrong module')
  else:m.pop(feature)
  (copy/'manifest.json').write_text(json.dumps(m));target=out/(name+'-zip')
  command=[sys.executable,str(ROOT/'standalone/archive_connection_test_package.py'),'--package',str(copy),'--output',str(target)]
  with (out/(name+'.log')).open('w') as log:r=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log)
  assert r.returncode!=0 and not target.exists(),name
  cases.append(dict(case=name,accepted=False,archive_started=False))
 base=json.loads(recipe.read_text())
 for name,flag in [('recipe-native-missing','--meta-shared-runtime' if meta else '--line-port'),('recipe-overlay-missing','--line-port-overlay'),('recipe-profile-mismatch','--chat-help')]:
  m=json.loads(json.dumps(base));m['terminal_flags'].remove(flag)
  path=out/(name+'.json');path.write_text(json.dumps(m));target=out/(name+'-build')
  command=[sys.executable,str(ROOT/'standalone/build_connection_candidate.py'),'--recipe',str(path),'--output-dir',str(target)]
  with (out/(name+'.log')).open('w') as log:r=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log)
  assert r.returncode!=0 and not target.exists(),name
  cases.append(dict(case=name,accepted=False,build_started=False))
 assert sha(terminal)==original['binary_sha256'] and sha(terminal.with_name(leaf))==original[descriptor]['sha256']
 result=dict(passed=True,module=a.module,cases=cases,terminal_sha256=sha(terminal),overlay_sha256=original[descriptor]['sha256'],package_manifest_sha256=sha(package/'manifest.json'),
  sources={n:sha(ROOT/n) for n in ('standalone/check_line_port_package_contract.py','standalone/package_connection_test.py','standalone/archive_connection_test_package.py','standalone/build_connection_candidate.py',str(recipe.relative_to(ROOT)))},
  scope=__doc__+' Actual immutable public products; bad companion/package/recipe fixtures are isolated copies and never executed. Separate DOS runtime and hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',a.module,'package contract:',len(cases),'cases')


if __name__=='__main__':main()
