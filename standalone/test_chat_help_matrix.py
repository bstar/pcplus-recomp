#!/usr/bin/env python3
"""24 real-DOS Chat Help success/repeat/resource-failure/flow sessions."""
import argparse,concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 out.mkdir(parents=True,exist_ok=False);bundle=json.loads((package/'package.json').read_text())
 names=['standalone/test_chat_help_matrix.py','standalone/test_chat_help_main.py','standalone/global_help_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py']
 sources={**bundle['sources'],**{name:sha(ROOT/name) for name in names}}
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 identity=hashlib.sha256(str(out.relative_to(ROOT)).encode()).hexdigest()[:12]
 def run(item):
  rows,case=item;name=f'r{rows}-{case}';target=out/(name+'-'+identity)
  with (out/(name+'.log')).open('w') as log:
   code=subprocess.run([sys.executable,str(ROOT/'standalone/test_chat_help_main.py'),'--package',str(package),'--output',str(target),'--rows',str(rows),'--case',case],cwd=ROOT,stdout=log,stderr=log).returncode
  file=target/'result.json';r=json.loads(file.read_text()) if file.exists() else None
  passed=code==0 and bool(r and r['passed'])
  if passed:
   assert (r['rows'],r['case'])==(rows,case) and r['products']==bundle['products'] and all(r['checks'].values())
   for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  print(name,'PASS' if passed else 'FAIL',flush=True)
  return dict(name=name,rows=rows,case=case,passed=passed,exit_code=code,receipt=str(file.relative_to(ROOT)) if file.exists() else None,receipt_sha256=sha(file) if file.exists() else None)
 items=[(rows,case) for rows in (25,28,43,50) for case in ('normal','repeat','missing-helper','missing-resource','bad-resource','flow')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,items))
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 report=dict(passed=all(r['passed'] for r in cases),cases=cases,products=bundle['products'],sources=sources,scope=__doc__+'25/28/43/50 rows; actual BIOS input, DOS child, full Chat/Help-or-error/Chat frames, cursor, unfinished input and resumed parser/UART. Flow changes exactly seven remote characters after observed XON. Two isolated processes at most. No product writes, physical/SIP/audio, busy parser/TEXT/queue or geometry-fault acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
