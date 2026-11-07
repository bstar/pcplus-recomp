#!/usr/bin/env python3
"""Cold source-only ALARM platform rebuild and selected real-I/O DOS repeats."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert all(p.is_relative_to(ROOT/'build') for p in (build,out));out.mkdir(exist_ok=False);fresh=out/'source';fresh.mkdir()
 expected=json.loads((build/'manifest.json').read_text());assert expected['passed'] and not expected['original_inputs'] and sha(build/'ALARM.EXE')==expected['binary_sha256']
 names={**expected['sources'],'standalone/test_alarm_dos_uart.py':sha(ROOT/'standalone/test_alarm_dos_uart.py'),'standalone/prove_alarm_dos_source.py':sha(Path(__file__))}
 for n,h in names.items():
  p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis','.git')
  assert p.suffix in ('.py','.c','.h','.asm','.inc') and sha(ROOT/n)==h,n
  dest=fresh/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dest)
 assert len([f for f in fresh.rglob('*') if f.is_file()])==len(names)
 (fresh/'build').mkdir();rebuilt=fresh/'build/rebuilt';tests=fresh/'build/tests'
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,str(fresh/'standalone/build_alarm_dos_uart.py'),'--output',str(rebuilt)],cwd=fresh,stdout=log,stderr=log,check=True)
  subprocess.run([sys.executable,str(fresh/'standalone/test_alarm_dos_uart.py'),'--build',str(rebuilt),'--output',str(tests),'--case','1-N-N-S','--case','2-S-K-E','--case','1-N-G-S'],cwd=fresh,stdout=log,stderr=log,check=True)
 actual=json.loads((rebuilt/'manifest.json').read_text());cases=json.loads((tests/'result.json').read_text())
 assert actual['binary_sha256']==expected['binary_sha256'] and cases['passed'] and len(cases['cases'])==3
 for n,h in names.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 report=dict(passed=True,source_files=len(names),sources=names,binary_sha256=actual['binary_sha256'],cases=[r['case'] for r in cases['cases']],test_result_sha256=sha(tests/'result.json'),original_inputs=[],
  scope=__doc__+' Empty declared-source tree without originals, private configuration, previous objects or Git metadata. Pinned Nix environment supplied by caller. Exact executable; normal real-PIT/UART completion, enhanced-key/software-flow and replacement-speaker-generation recovery repeated. Not a repeat of the complete50-case matrix or physical/VM acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cold ALARM DOS platform:',len(names),'sources,3 real-I/O cases')
if __name__=='__main__':main()
