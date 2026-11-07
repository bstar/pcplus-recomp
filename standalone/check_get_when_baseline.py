#!/usr/bin/env python3
"""Compare GET-disabled ALARM diagnostic against the pre-GET WHEN source."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_get_when_uart import ROOT,sha
BASELINE='f2fd97b'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'manifest.json').read_text());assert expected['passed'] and expected['original_inputs']==[] and sha(build/'ALARM.EXE')==expected['binary_sha256']
 out.mkdir();fresh=out/'source';replaced={}
 for name,digest in expected['sources'].items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone','reconstruction') and sha(ROOT/path)==digest
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 for name in ('src/aspect/when_runtime.c','src/aspect/when_runtime.h'):
  prior=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT);(fresh/name).write_bytes(prior)
  replaced[name]=dict(current=sha(ROOT/name),baseline=sha(fresh/name))
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 (fresh/'build').mkdir()
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_alarm_when_uart.py','--output','build/prior'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=sha(fresh/'build/prior/ALARM.EXE');assert actual==expected['binary_sha256']
 result=dict(passed=True,original_inputs=[],baseline_revision=BASELINE,replaced=replaced,sources=expected['sources'],source_count=len(expected['sources']),binary_sha256=actual,current_manifest_sha256=sha(build/'manifest.json'),scope=__doc__+' Two pre-change public source files; all other declared inputs identical. Exact GET-disabled ALARM EXE only, not whole application/shipping rebuild or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS GET-disabled ALARM baseline:',actual)

if __name__=='__main__':main()
