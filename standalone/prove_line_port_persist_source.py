#!/usr/bin/env python3
"""Reproduce persistence diagnostics from a declared public-source export."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();receipt=a.receipt.resolve();out=a.output.resolve()
 assert receipt.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 prior=json.loads(receipt.read_text());assert prior['passed']
 out.mkdir(parents=True,exist_ok=False);tree=out/'tree'
 for name,digest in prior['sources'].items():
  assert sha(ROOT/name)==digest,name
  target=tree/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 run=tree/'build/persistence'
 subprocess.run([sys.executable,str(tree/'standalone/test_line_port_persist_dos.py'),'--output',str(run)],cwd=tree,check=True)
 result=json.loads((run/'result.json').read_text())
 assert result['passed'] and result['checks']==prior['checks'] and result['binaries']==prior['binaries']
 assert result['target_sha256']==prior['target_sha256']
 report=dict(passed=True,sources=prior['sources'],binaries=result['binaries'],checks=result['checks'],
  target_sha256=result['target_sha256'],input_receipt_sha256=sha(receipt),
  scope='Ten declared public files only; actual DOS real/fault diagnostics repeat with exact EXEs and output bytes. No original/private/analysis/prior object/Git metadata in export; outer pinned Nix supplies tools.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Persistence isolated source proof: 10 files; both EXEs and complete target bytes exact')


if __name__=='__main__':main()
