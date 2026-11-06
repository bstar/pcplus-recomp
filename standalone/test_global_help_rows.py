#!/usr/bin/env python3
"""Exercise actual terminal/PCHELP ownership at all four supported heights."""
import argparse,concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--workers',type=int,choices=(1,2),default=2)
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 out.mkdir(parents=True,exist_ok=False)
 bundle=json.loads((package/'package.json').read_text())
 names=['standalone/test_global_help_rows.py','standalone/test_global_help_main.py','standalone/global_help_watch.asm']
 frozen={**bundle['sources'],**{name:sha(ROOT/name) for name in names}}
 for name,digest in frozen.items():assert sha(ROOT/name)==digest,name
 for name,digest in bundle['products'].items():assert sha(package/name)==digest,name
 identity=hashlib.sha256(str(out.relative_to(ROOT)).encode()).hexdigest()[:12]
 def run(item):
  rows,case=item;name=f'rows{rows}-{case}';target=out/(name+'-'+identity)
  with (out/(name+'.log')).open('w') as log:
   code=subprocess.run([sys.executable,str(ROOT/'standalone/test_global_help_main.py'),'--package',str(package),'--output',str(target),'--case',case,'--rows',str(rows)],cwd=ROOT,stdout=log,stderr=log).returncode
  file=target/'result.json';r=json.loads(file.read_text()) if file.exists() else None
  passed=code==0 and bool(r and r['passed'])
  if passed:
   assert r['products']==bundle['products'] and r['rows']==rows and r['case']==case
   assert all(r['checks'].values()) and r['checks']['actual_BIOS_rows']
   for path,digest in r['sources'].items():assert sha(ROOT/path)==digest,path
  print(name,'PASS' if passed else 'FAIL',flush=True)
  return dict(name=name,rows=rows,case=case,passed=passed,exit_code=code,receipt=str(file.relative_to(ROOT)) if file.exists() else None,receipt_sha256=sha(file) if file.exists() else None)
 cases=[(rows,case) for rows in (25,28,43,50) for case in ('normal','repeat','missing-helper','missing-resource','bad-resource','flow')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:results=list(pool.map(run,cases))
 for name,digest in frozen.items():assert sha(ROOT/name)==digest,name
 report=dict(passed=all(r['passed'] for r in results),products=bundle['products'],sources=frozen,cases=results,
  scope='24 independent actual DOS8086 normal-main sessions:25/28/43/50 rows times success/repeat/missing helper/missing HLP/malformed HLP/flow. Actual BDA height, complete saved reference frame/cursor, helper footer at actual last row, resumed keys/parser and hardware restore. Two isolated DOS processes at most; no product memory writes. No original helper comparison at28/43 rows or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
