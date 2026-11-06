#!/usr/bin/env python3
"""Source-only DOS Help regression against captured original VGA/cursor hashes."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def inventory(manifest):
 names=set(manifest['sources'])|{
  'standalone/test_help_program_source.py','standalone/fixtures/help_program_vga.json',
  'standalone/capture_help_screen.py','standalone/help_screen_observer.asm','standalone/help_screen_parent.c',
  'standalone/context_help_parent.c','standalone/context_help_child.c','standalone/context_help_state.asm',
  'reconstruction/context_help/provenance.json','reconstruction/program_exec/provenance.json','reconstruction/uart/encodings.inc',
  'reconstruction/context_help/handoff.asm','reconstruction/program_exec/strcpy.asm','reconstruction/program_exec/get_ds.asm'}
 return {name:sha(ROOT/name) for name in sorted(names)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cold',action='store_true');a=p.parse_args()
 build=a.build.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((build/'manifest.json').read_text())
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 for name,digest in manifest['products'].items():assert sha(build/name)==digest,name
 sources=inventory(manifest)
 if a.cold:
  for name,digest in sources.items():
   target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target);assert sha(target)==digest
  with (out/'build.log').open('w') as log:
   subprocess.run([sys.executable,str(out/'source/standalone/build_help_program.py'),'--output',str(out/'build')],cwd=out/'source',stdout=log,stderr=log,check=True)
  assert json.loads((out/'build/manifest.json').read_text())==manifest
  with (out/'tests.log').open('w') as log:
   subprocess.run([sys.executable,str(out/'source/standalone/test_help_program_source.py'),'--build',str(out/'build'),'--output',str(out/'tests')],cwd=out/'source',stdout=log,stderr=log,check=True)
  tests=json.loads((out/'tests/result.json').read_text());assert tests['passed']
  report=dict(passed=True,cold=True,source_files=len(sources),sources=sources,products=manifest['products'],tests=tests,scope='Isolated public-source rebuild and all recorded source-only Help VGA/cursor/restore sessions, using original-derived hashes and authored test resources. No originals, configurations, previous objects or analysis artifacts copied.')
 else:
  golden=json.loads((ROOT/'standalone/fixtures/help_program_vga.json').read_text());runs=[]
  for case in golden['entries']:
   label=str(case['rows'])+'-'+case['case'];dest=out/label
   with (out/(label+'.log')).open('w') as log:
    subprocess.run([sys.executable,str(ROOT/'standalone/capture_help_screen.py'),'--helper',str(build/'PCHELP.RTE'),'--output',str(dest),'--rows',str(case['rows']),'--keys',json.dumps(case['keys']),'--topic',str(case['topic'])],stdout=log,stderr=log,check=True)
   actual=json.loads((dest/'result.json').read_text())
   checks={name:actual[name]==case[name] for name in ['frames','captures','metadata','restored','resource_sha256']}
   checks['child_success']=actual['child_exit_code']==0
   runs.append(dict(case=label,passed=all(checks.values()),checks=checks,result_sha256=sha(dest/'result.json'),actual=actual))
   print(label,'PASS' if runs[-1]['passed'] else 'FAIL',flush=True)
  report=dict(passed=all(run['passed'] for run in runs),cold=False,sources=sources,products=manifest['products'],golden_sha256=sha(ROOT/'standalone/fixtures/help_program_vga.json'),runs=runs,scope='Actual source-only DOS helper sessions, matching authored-resource original-derived VGA hashes, BDA cursor states and exact background/cursor restoration. No original executable/HLP or analysis artifact read. Selected workflows, not complete helper/application/physical parity.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
