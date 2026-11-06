#!/usr/bin/env python3
"""Twelve DOS component Help-admission faults using real BIOS transitions."""
import argparse,concurrent.futures,json,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('terminal','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256'] and m['experimental_chat_help']
 names=['standalone/test_chat_help_geometry_matrix.py','standalone/test_chat_help_geometry.py','standalone/chat_help_geometry_host.c','standalone/chat_parent_invoke.asm']
 sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 def run(item):
  rows,fault=item;name=f'r{rows}-f{fault}';target=out/(out.name+'-'+name)
  with (out/(name+'.log')).open('w') as log:
   code=subprocess.run([sys.executable,str(ROOT/'standalone/test_chat_help_geometry.py'),'--terminal',str(binary),'--output',str(target),'--rows',str(rows),'--fault',str(fault)],cwd=ROOT,stdout=log,stderr=log).returncode
  path=target/'result.json';r=json.loads(path.read_text()) if path.exists() else None;passed=code==0 and bool(r and r['passed'])
  if passed:
   assert r['binary_sha256']==m['binary_sha256'] and (r['rows'],r['fault'])==(rows,fault)
   for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  print(name,'PASS' if passed else 'FAIL',flush=True)
  return dict(rows=rows,fault=fault,passed=passed,receipt=str(path.relative_to(ROOT)) if path.exists() else None,receipt_sha256=sha(path) if path.exists() else None,exit_code=code)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,[(r,f) for r in (25,28,43,50) for f in (0,1,2)]))
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 result=dict(passed=all(r['passed'] for r in cases),binary_sha256=m['binary_sha256'],module_sha256=m['chat_loader']['module']['binary_sha256'],sources=sources,cases=cases,scope=__doc__+'Supplied canonical startup; exact loaded parent/module entries on parent DS=SS/stack. Height/page/graphics guards and clean underlay retirement. Valid Help only queued; no main/DOS EXEC or reconstruction of externally erased live Chat pixels.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
