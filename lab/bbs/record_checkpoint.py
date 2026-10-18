#!/usr/bin/env python3
"""Record one explicit local test label, retaining prior runtime evidence."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads(path.read_text())
def artifacts(folder):
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir()) if p.is_file()}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--menus');parser.add_argument('--editors',required=True);parser.add_argument('--editors-only',action='store_true',help='Update only editor evidence; preserve separately tested menu runtimes');parser.add_argument('--enigma-menus');parser.add_argument('--enigma-editors');parser.add_argument('--prior-enigma-editors',action='append',default=[],help='Retain additional same-runtime editor attempts before selecting the current run')
 parser.add_argument('--prior-synchronet-editors',action='append',default=[],help='Retain additional same-runtime Synchronet configuration/preparation attempts')
 args=parser.parse_args()
 assert args.editors_only or args.menus,'--menus is required unless --editors-only is selected'
 digest=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest()
 if not args.editors_only:
  matrix=read(ROOT/'docs/validation/bbs-matrix.json')
  for name in ('synchronet','enigma','mystic'):
   entry=matrix['servers'][name];folder=ROOT/'build/bbs-lab/results'/name/(args.enigma_menus if name=='enigma' and args.enigma_menus else args.menus)
   run=read(folder/'result.json');assert run['binary_sha256']==digest
   audit=read(folder/({'synchronet':'navigation-checks.json','enigma':'semantic-audit.json','mystic':'mystic-audit.json'}[name]))
   assert audit.get('binary_sha256',audit.get('DOS_binary_sha256'))==digest
   prior={key:entry[key] for key in ('result','semantic_evidence','retained_artifacts')}
   entry.setdefault('prior_runtime_cases',[]).append(prior)
   entry.update(result=run,semantic_evidence=audit,retained_artifacts=artifacts(folder))
  matrix.update(binary_sha256=digest,passed=all(s['result']['passed'] and s['semantic_evidence']['passed'] for s in matrix['servers'].values()))
 editors=read(ROOT/'docs/validation/bbs-editors.json')
 for name in ('synchronet','enigma'):
  entry=editors['servers'][name];folder=ROOT/'build/bbs-lab/results'/name/(args.enigma_editors if name=='enigma' and args.enigma_editors else args.editors)
  run=read(folder/'result.json');audit=read(folder/'semantic-audit.json');assert run['binary_sha256']==audit['binary_sha256']==digest
  prior={key:entry[key] for key in ('run','semantic_evidence','retained_artifacts')}
  selected=dict(run=run,semantic_evidence=audit,retained_artifacts=artifacts(folder))
  if prior!=selected:entry.setdefault('prior_runtime_cases',[]).append(prior)
  if name in ('enigma','synchronet'):
   for label in (args.prior_enigma_editors if name=='enigma' else args.prior_synchronet_editors):
    assert label and all(c.isalnum() or c in '-_' for c in label)
    earlier=ROOT/'build/bbs-lab/results'/name/label
    earlier_run=read(earlier/'result.json');earlier_audit=read(earlier/'semantic-audit.json')
    assert earlier_run['binary_sha256']==earlier_audit['binary_sha256']==digest
    retained=dict(run=earlier_run,semantic_evidence=earlier_audit,retained_artifacts=artifacts(earlier))
    if retained not in entry.setdefault('prior_runtime_cases',[]):entry['prior_runtime_cases'].append(retained)
  entry.update(selected)
 editors.update(binary_sha256=digest,passed=all(s['run']['passed'] and s['semantic_evidence']['passed'] for s in editors['servers'].values()))
 if not args.editors_only:(ROOT/'docs/validation/bbs-matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
 (ROOT/'docs/validation/bbs-editors.json').write_text(json.dumps(editors,indent=2)+'\n')
 print('Recorded',digest,'menus',('unchanged' if args.editors_only else matrix['passed']),'editors',editors['passed'])
if __name__=='__main__':main()
