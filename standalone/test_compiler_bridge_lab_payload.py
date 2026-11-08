#!/usr/bin/env python3
"""Reject missing, damaged or undeclared compiler companions in a lab payload."""
import argparse,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import companions,select_product,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('payload','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();payload=a.payload.resolve();out=a.output.resolve()
 assert payload.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 package=json.loads((payload/'package.json').read_text())
 assert package['passed'] and package['release_eligible'] is False
 binary,sources=select_product(payload/'TERMINAL.EXE','TERMINAL.EXE')
 assert {p.name for p in companions(binary)}=={'PCCOMP.OVL','PCLINE.OVL','PCMETA.OVL','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP'}
 for name,digest in package['products'].items():assert sha(payload/name)==digest,name
 out.mkdir();checks={'all_nine_matched_lab_products':len(package['products'])==9,'compiler_module_staged':True}
 for fault in ('missing','truncated','corrupt','undeclared'):
  folder=out/fault;folder.mkdir()
  for leaf in (*package['products'],'manifest.json','package.json','terminal.map'):shutil.copyfile(payload/leaf,folder/leaf)
  module=folder/'PCCOMP.OVL'
  if fault=='missing':module.unlink()
  elif fault=='truncated':module.write_bytes(module.read_bytes()[:-1])
  elif fault=='corrupt':data=bytearray(module.read_bytes());data[-1]^=1;module.write_bytes(data)
  else:
   manifest=json.loads((folder/'manifest.json').read_text());manifest.pop('experimental_compiler_lease_module')
   (folder/'manifest.json').write_text(json.dumps(manifest))
   # Keep the unrelated Help-bundle binding coherent, so this case isolates
   # the missing mandatory compiler declaration rather than a generic hash.
   bundle=json.loads((folder/'package.json').read_text());bundle['parent_manifest_sha256']=sha(folder/'manifest.json')
   (folder/'package.json').write_text(json.dumps(bundle))
  try:companions(folder/'TERMINAL.EXE')
  except (AssertionError,OSError,KeyError):checks['reject_'+fault]=True
  else:checks['reject_'+fault]=False
 result=dict(passed=all(checks.values()),checks=checks,products=package['products'],
  checker_sha256=sha(Path(__file__)),resolver_sha256=sha(ROOT/'lab/bbs/product_inputs.py'),original_inputs=[],
  scope=__doc__+' File-contract failures only; no DOS, BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
