#!/usr/bin/env python3
"""Reject incompatible renderer/compiler modules and incomplete public archives."""
import argparse,copy,json,shutil,subprocess,sys,zlib
from pathlib import Path
from package_connection_test import ROOT,sha,render_capability,validate_render_pair,compiler_module_contract


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','runner','package','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 parent=json.loads(a.terminal.with_name('manifest.json').read_text());child=json.loads(a.runner.with_name('manifest.json').read_text())
 assert sha(a.terminal)==parent['binary_sha256'] and sha(a.runner)==child['binary_sha256']
 cap=render_capability(a.terminal);assert cap==23
 cases=[]
 def check(name,fn,accepted=False):
  try:fn();actual=True
  except (AssertionError,FileNotFoundError,KeyError):actual=False
  assert actual==accepted,name
  cases.append(dict(case=name,accepted=actual))
 check('matched-pair',lambda:validate_render_pair(cap,parent,child),True)
 for side,flags in ((parent,('experimental_compiler_lease_bridge','experimental_compiler_lease_arena','experimental_aspect_get_policy','experimental_aspect_get_display','experimental_aspect_emulate_policy','experimental_aspect_snapshot_lease')),
                    (child,('experimental_compiler_parent_lease','experimental_get_VM','experimental_get_policy','experimental_get_display','experimental_emulate_VM','experimental_alarm_VM','experimental_snapshot_lease'))):
  for flag in flags:
   changed=copy.deepcopy(side);changed[flag]=False
   check('missing-'+flag,lambda:validate_render_pair(cap,changed if side is parent else parent,changed if side is child else child))
 for version in (20,21,22,24):check('wrong-capability-'+str(version),lambda:validate_render_pair(version,parent,child))
 fixture=out/'module';fixture.mkdir()
 for leaf in ('TERMINAL.EXE','terminal.map','PCCOMP.OVL'):shutil.copyfile(a.terminal.with_name(leaf),fixture/leaf)
 blob=(fixture/'PCCOMP.OVL').read_bytes()
 for name in ('valid','missing','truncated','corrupt','undeclared','bridge-disabled','wrong-size','wrong-fixups','forged-body'):
  m=copy.deepcopy(parent);path=fixture/'PCCOMP.OVL';path.write_bytes(blob)
  if name=='missing':path.unlink()
  elif name=='truncated':path.write_bytes(blob[:-1])
  elif name in ('corrupt','forged-body'):
   data=bytearray(blob);data[0]^=1;path.write_bytes(data)
   if name=='forged-body':m['experimental_compiler_lease_module'].update(sha256=sha(path),crc32=f'{zlib.crc32(data):08x}')
  elif name=='undeclared':m.pop('experimental_compiler_lease_module')
  elif name=='bridge-disabled':m['experimental_compiler_lease_bridge']=False
  elif name=='wrong-size':m['experimental_compiler_lease_module']['bank_bytes']-=1
  elif name=='wrong-fixups':m['experimental_compiler_lease_module']['relocations']+=1
  check('module-'+name,lambda:compiler_module_contract(fixture/'TERMINAL.EXE',m),name=='valid')
 package=json.loads((a.package/'manifest.json').read_text());directory=package['dos_directory']
 for name in ('valid','missing','corrupt','undeclared','wrong-capability','no-descriptor','forged-hash'):
  folder=out/('archive-'+name);shutil.copytree(a.package,folder);m=copy.deepcopy(package);path=folder/directory/'PCCOMP.OVL'
  if name=='missing':m['files'].pop('PCCOMP.OVL')
  elif name in ('corrupt','forged-hash'):
   path.write_bytes(b'bad module')
   if name=='forged-hash':m['files']['PCCOMP.OVL']=m['compiler_lease_module']['sha256']=sha(path)
  elif name=='undeclared':m.pop('experimental_compiler_lease_bridge')
  elif name=='wrong-capability':m['parent_render_capability']=20
  elif name=='no-descriptor':m.pop('compiler_lease_module')
  (folder/'manifest.json').write_text(json.dumps(m));target=out/(name+'-zip')
  with (out/(name+'.log')).open('w') as log:
   r=subprocess.run([sys.executable,str(ROOT/'standalone/archive_connection_test_package.py'),'--package',str(folder),'--output',str(target)],stdout=log,stderr=log)
  assert (r.returncode==0)==(name=='valid') and target.exists()==(name=='valid'),name
  cases.append(dict(case='archive-'+name,accepted=name=='valid'))
 text=(a.package/directory/'README.TXT').read_bytes()
 assert b'PCCOMP.OVL' in text and b'Alt-F5 accepts source ASP' in text and b'Automatic resident compilation and nested PROGRAM remain separate gates.' not in text
 for leaf,digest in package['files'].items():assert sha(a.package/directory/leaf)==digest
 names=['standalone/check_compiler_bridge_package.py','standalone/package_connection_test.py','standalone/archive_connection_test_package.py']
 r=dict(passed=True,cases=cases,products={n:package['files'][n] for n in ('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PCCOMP.OVL')},sources={n:sha(ROOT/n) for n in names},package_manifest_sha256=sha(a.package/'manifest.json'),original_inputs=[],scope=__doc__+' Isolated source-built fixtures only. Corrupt modules/packages never execute; physical and runtime admission remain separate.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS compiler-bridge package:',len(cases),'cases')


if __name__=='__main__':main()
