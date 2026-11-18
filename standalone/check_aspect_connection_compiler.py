#!/usr/bin/env python3
"""Match scripted connection grammar against frozen original and DOS outputs.

Only source-built ASPCOMP executes here. Runtime command ownership is separate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import CompileError,compile_source


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--compiler',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();folder=a.compiler.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads((folder/'manifest.json').read_text())
 assert not manifest['original_inputs'] and sha(folder/'ASPCOMP.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 fixture=ROOT/'standalone/fixtures/aspect_connection_compiler_vectors.json'
 oracle=json.loads(fixture.read_text());cases=oracle['cases']
 assert oracle['compiler_sha256']=='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
 assert len(cases)==311 and sum(c['success'] for c in cases)==82
 assert len({c['source_sha256'] for c in cases})==len(cases)
 assert set(oracle['command_grammar'])=={'dial','mdial','redial','hangup'}
 out.mkdir();shutil.copyfile(folder/'ASPCOMP.EXE',out/'ASPCOMP.EXE');batch=['@echo off']
 for i,c in enumerate(cases):
  assert hashlib.sha256(c['source'].encode('cp437')).hexdigest()==c['source_sha256']
  try:actual=compile_source(c['source']);success=True
  except CompileError:actual=b'';success=False
  assert success==c['success'],c['label']
  if success:assert actual.hex()==c['hex'] and hashlib.sha256(actual).hexdigest()==c['asx_sha256'],c['label']
  else:assert c['errors'],c['label']
  leaf=f'P{i:05}';(out/(leaf+'.ASP')).write_bytes(c['source'].replace('\n','\r\n').encode('cp437'))
  batch += [f'ASPCOMP {leaf}.ASP >{leaf}.LOG',f'if errorlevel 1 echo REJECT>{leaf}.RES',f'if not errorlevel 1 echo ACCEPT>{leaf}.RES']
 (out/'RUN.BAT').write_bytes(('\r\n'.join(batch+['echo COMPLETE>DONE.TXT'])+'\r\n').encode('ascii'))
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n'+f'mount c "{out}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 assert (out/'DONE.TXT').read_text().strip()=='COMPLETE'
 records=[]
 for i,c in enumerate(cases):
  leaf=f'P{i:05}';target=out/(leaf+'.ASX');success=(out/(leaf+'.RES')).read_text().strip()=='ACCEPT'
  assert success==c['success']==target.exists(),c['label']
  if success:assert target.read_bytes()==bytes.fromhex(c['hex']) and sha(target)==c['asx_sha256'],c['label']
  records.append(dict(label=c['label'],accepted=success,source_sha256=c['source_sha256'],asx_sha256=sha(target) if success else None,log_sha256=sha(out/(leaf+'.LOG'))))
 sources=dict(manifest['sources'])
 for path in [Path(__file__),fixture,ROOT/'src/aspect/compiler.py']:sources[str(path.relative_to(ROOT))]=sha(path)
 report=dict(passed=True,cases=records,case_count=len(cases),accepted=82,rejected=229,
  original_observations=oracle['original_observations'],original_compiler_sha256=oracle['compiler_sha256'],
  binary_sha256=manifest['binary_sha256'],compiler_manifest_sha256=sha(folder/'manifest.json'),sources=sources,original_inputs=[],
  scope=__doc__+' Original320 observations/311 unique sources across four commands: exact optional-string roles, locals/parameters/S0, readonly inputs, types/arity/atomic-expression refusals, reserved declarations and whitespace/comma boundaries. Accepted ASX bytes agree across original and both maintained compilers. Original binaries are not read. No native runtime, script dialing, UART, BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS311 original connection compiler cases:82 accepted,229 rejected')


if __name__=='__main__':main()
