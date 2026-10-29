#!/usr/bin/env python3
"""Rebuild six pre-script variants and preserve their accepted executable bytes."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from package_special_edition import ROOT,commands_for,products_for
CASES=[({},'bd86a10b94544007242d2ce6bb737be5ab90909d4fcf2bac8713120d2b2ffa10'),
 (dict(custom_irq=True,directory_storage=True),'4c23fa0750e65c857435d5d587cbeba30a0fe42a85da9951bc15e61352c1f589'),
 (dict(custom_irq=True,directory_resource_cli=True),'a89f4382bc01fec3c62cc20e42e2bdd15ba77c78ee86bd05021d953be5ad9869'),
 (dict(custom_irq=True,directory_resource_owner=True),'e718b0bce67cd0fb86b7f8ca049a3ae429e13a7b6ea1033ce2fb012450cbdbbe'),
 (dict(custom_irq=True,directory_retirement=True),'fb36d39ecc4beaeb7a7ae3c1fd07eb2fe31c949516324b8f71962f30e6fa1e91'),
 (dict(custom_irq=True,directory_translation=True),'473418b7b869d8047957db1439e28ab990493303f379ece9656d39631d589336')]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);reports=[]
 for flags,expected in CASES:
  folder=products_for(**flags)['TERMINAL.EXE'] if flags else 'terminal'
  command=commands_for(**flags)[0] if flags else [sys.executable,'standalone/build_terminal.py']
  subprocess.run(command,cwd=ROOT,check=True);actual=sha(ROOT/'build'/folder/'TERMINAL.EXE')
  reports.append(dict(variant=folder,flags=flags,expected_sha256=expected,sha256=actual,unchanged=actual==expected));assert actual==expected,(folder,actual,expected)
 result=dict(passed=True,original_inputs=[],controls=reports,sources={n:sha(ROOT/n) for n in ['standalone/check_directory_script_controls.py','standalone/package_special_edition.py','standalone/build_terminal.py']})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS six unchanged control executables')
if __name__=='__main__':main()
