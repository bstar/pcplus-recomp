#!/usr/bin/env python3
"""Real native-wait Help admission at all heights, including a full32-key FIFO."""
import argparse,concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 bundle=json.loads((package/'package.json').read_text())
 names=['standalone/test_chat_help_busy_matrix.py','standalone/test_chat_help_busy.py','standalone/chat_help_life_watch.asm','standalone/chat_busy_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py']
 sources={**bundle['sources'],**{n:sha(ROOT/n) for n in names}}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 identity=hashlib.sha256(str(out.relative_to(ROOT)).encode()).hexdigest()[:12]
 def run(item):
  rows,keys=item;name=f'r{rows}-keys{keys}';target=out/(name+'-'+identity)
  with (out/(name+'.log')).open('w') as log:
   code=subprocess.run([sys.executable,str(ROOT/'standalone/test_chat_help_busy.py'),'--package',str(package),'--output',str(target),'--rows',str(rows),'--keys',str(keys)],cwd=ROOT,stdout=log,stderr=log).returncode
  file=target/'result.json';r=json.loads(file.read_text()) if file.exists() else None;passed=code==0 and bool(r and r['passed'])
  if passed:
   assert r['products']==bundle['products'] and (r['rows'],r['ordinary_keys'])==(rows,keys) and all(r['checks'].values()) and not r['observer_damage']
   for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  print(name,'PASS' if passed else 'FAIL',flush=True)
  return dict(rows=rows,keys=keys,passed=passed,receipt=str(file.relative_to(ROOT)) if file.exists() else None,receipt_sha256=sha(file) if file.exists() else None,exit_code=code)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,[(r,k) for r in (25,28,43,50) for k in (1,31)]))
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=all(r['passed'] for r in cases),products=bundle['products'],cases=cases,sources=sources,scope=__doc__+' Eight independent DOS8086 normal-main sessions, real delayed CSI/native parser, BIOS/FIFO Alt-Z, actual helper and exact sampled loaded code/PROGRAM frame return. No product writes, continuous-lifetime/geometry-fault/physical/SIP/audio acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
