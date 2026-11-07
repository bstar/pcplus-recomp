#!/usr/bin/env python3
"""Rebuild GET lease diagnostic and repeat selected wire tests in a clean export."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_get_when_uart import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'manifest.json').read_text());assert expected['passed'] and expected['original_inputs']==[]
 names=expected['sources']|{'standalone/test_get_when_uart.py':sha(ROOT/'standalone/test_get_when_uart.py')}
 out.mkdir();fresh=out/'source'
 for name,digest in names.items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone','reconstruction')
  assert path.suffix in ('.py','.asm','.c','.h','.inc') and sha(ROOT/path)==digest
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/build_get_when_uart.py','--output','build/diagnostic'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/diagnostic/manifest.json').read_text());assert actual==expected
 cases=['1-N-A-S','2-S-C-E','1-S-F-E']
 command=[sys.executable,'standalone/test_get_when_uart.py','--build','build/diagnostic','--output','build/tests']
 for case in cases:command+=['--case',case]
 with (out/'tests.log').open('w') as log:subprocess.run(command,cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 result=json.loads((fresh/'build/tests/result.json').read_text());assert result['passed'] and result['binary_sha256']==expected['binary_sha256'] and [r['case'] for r in result['cases']]==cases
 for name,digest in names.items():assert sha(ROOT/name)==sha(fresh/name)==digest
 report=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,sources=names,source_count=len(names),binary_sha256=actual['binary_sha256'],repeated_cases=cases,test_result_sha256=sha(fresh/'build/tests/result.json'),scope=__doc__+' Exact diagnostic binary; real DOS BIOS/UART with synthetic native WHEN/parent receive entry. No live application/physical acceptance. Outer pinned Nix provides tools.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS GET lease export:',len(names),'public inputs; exact EXE; three wire cases')

if __name__=='__main__':main()
