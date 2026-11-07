#!/usr/bin/env python3
"""Exercise Alt-P companion admission and reject incomplete public packages."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha,terminal_companions


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','package','recipe','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 terminal=a.terminal.resolve();package=a.package.resolve();recipe=a.recipe.resolve()
 assert terminal.is_relative_to(ROOT/'build') and package.is_relative_to(ROOT/'build') and recipe.is_relative_to(ROOT)
 original=json.loads(terminal.with_name('manifest.json').read_text());assert sha(terminal)==original['binary_sha256']
 fixture=out/'product';fixture.mkdir()
 for name in ('TERMINAL.EXE','PCLINE.OVL','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP','package.json'):
  shutil.copyfile(terminal.with_name(name),fixture/name)
 blob=(fixture/'PCLINE.OVL').read_bytes();cases=[]
 for name in ('valid','missing','corrupt','flag-missing','descriptor-missing','native-missing','layout-missing','plain-control'):
  m=json.loads(json.dumps(original));(fixture/'PCLINE.OVL').write_bytes(blob)
  if name=='missing':(fixture/'PCLINE.OVL').unlink()
  elif name=='corrupt':(fixture/'PCLINE.OVL').write_bytes(bytes([blob[0]^1])+blob[1:])
  elif name=='flag-missing':m['experimental_line_port_overlay']=False
  elif name=='descriptor-missing':del m['line_port_overlay']
  elif name=='native-missing':m['experimental_line_port']=False
  elif name=='layout-missing':m['memory_layout']['line_port_overlay_contract_verified']=False
  elif name=='plain-control':
   for key in ('line_port_overlay','experimental_line_port_overlay','experimental_line_port','experimental_global_help','experimental_chat_loader'):m.pop(key,None)
  try:files,_=terminal_companions(fixture/'TERMINAL.EXE',m);accepted=True
  except (AssertionError,FileNotFoundError):accepted=False
  assert accepted==(name in ('valid','plain-control')),name
  if name=='valid':assert files['PCLINE.OVL'].read_bytes()==blob
  if name=='plain-control':assert files=={}
  cases.append(dict(case=name,accepted=accepted))
 for name in ('archive-missing','archive-corrupt','archive-undeclared'):
  copy=out/name;shutil.copytree(package,copy);m=json.loads((copy/'manifest.json').read_text())
  if name=='archive-missing':del m['files']['PCLINE.OVL']
  elif name=='archive-corrupt':(copy/m['dos_directory']/'PCLINE.OVL').write_bytes(b'wrong module')
  else:m.pop('experimental_line_port_overlay')
  (copy/'manifest.json').write_text(json.dumps(m));target=out/(name+'-zip')
  command=[sys.executable,str(ROOT/'standalone/archive_connection_test_package.py'),'--package',str(copy),'--output',str(target)]
  with (out/(name+'.log')).open('w') as log:r=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log)
  assert r.returncode!=0 and not target.exists(),name
  cases.append(dict(case=name,accepted=False,archive_started=False))
 base=json.loads(recipe.read_text())
 for name,flag in [('recipe-native-missing','--line-port'),('recipe-overlay-missing','--line-port-overlay'),('recipe-profile-mismatch','--chat-help')]:
  m=json.loads(json.dumps(base));m['terminal_flags'].remove(flag)
  path=out/(name+'.json');path.write_text(json.dumps(m));target=out/(name+'-build')
  command=[sys.executable,str(ROOT/'standalone/build_connection_candidate.py'),'--recipe',str(path),'--output-dir',str(target)]
  with (out/(name+'.log')).open('w') as log:r=subprocess.run(command,cwd=ROOT,stdout=log,stderr=log)
  assert r.returncode!=0 and not target.exists(),name
  cases.append(dict(case=name,accepted=False,build_started=False))
 assert sha(terminal)==original['binary_sha256'] and sha(terminal.with_name('PCLINE.OVL'))==original['line_port_overlay']['sha256']
 result=dict(passed=True,cases=cases,terminal_sha256=sha(terminal),overlay_sha256=original['line_port_overlay']['sha256'],package_manifest_sha256=sha(package/'manifest.json'),
  sources={n:sha(ROOT/n) for n in ('standalone/check_line_port_package_contract.py','standalone/package_connection_test.py','standalone/archive_connection_test_package.py','standalone/build_connection_candidate.py',str(recipe.relative_to(ROOT)))},
  scope=__doc__+' Actual immutable public products; bad companion/package/recipe fixtures are isolated copies and never executed. Separate DOS runtime and hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS Alt-P package contract:',len(cases),'cases')


if __name__=='__main__':main()
