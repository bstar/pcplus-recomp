#!/usr/bin/env python3
"""Compare compiler-boundary behavior against the unchanged reviewed launcher."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('baseline','candidate','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 b=json.loads((a.baseline/'checks.json').read_text());c=json.loads((a.candidate/'checks.json').read_text())
 assert b['passed'] and c['passed'] and b['compiler_sha256']==c['compiler_sha256']
 assert b['checker_sha256']==c['checker_sha256']==sha(ROOT/'standalone/check_aspect_source_compile.py')
 assert b['test_inputs']==c['test_inputs'] and b['DOS_summary']==c['DOS_summary']
 names=sorted(p.name for p in (a.baseline/'tests').iterdir() if p.suffix in ('.OUT','.ERR'))
 assert len(names)==48 and set(names)=={p.name for p in (a.candidate/'tests').iterdir() if p.suffix in ('.OUT','.ERR')}
 hashes={}
 for n in names:
  assert (a.baseline/'tests'/n).read_bytes()==(a.candidate/'tests'/n).read_bytes(),n
  hashes[n]=sha(a.candidate/'tests'/n)
 out.mkdir();r=dict(passed=True,original_inputs=[],baseline_sha256=b['runner_sha256'],candidate_sha256=c['runner_sha256'],
  compiler_sha256=c['compiler_sha256'],DOS_summary=c['DOS_summary'],output_files=len(names),outputs=hashes,
  sources={'standalone/compare_compiler_exec.py':sha(__file__),'standalone/check_aspect_source_compile.py':sha(ROOT/'standalone/check_aspect_source_compile.py')},
  baseline_report_sha256=sha(a.baseline/'checks.json'),candidate_report_sha256=sha(a.candidate/'checks.json'),
  scope=__doc__+' Exact stdout/stderr for24 cases, same source fixtures; both reports also verify parent PSP/vectors and20 counted replacements. Not complete runtime/environment/process equivalence or physical/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS compiler exec equivalence:',len(names),'exact outputs;',c['DOS_summary'])
if __name__=='__main__':main()
