#!/usr/bin/env python3
"""Run the actual DOS nearheap owner and independent ownership regressions."""
import json,os,re,subprocess
from pathlib import Path
from build_aspect_find_owner import ROOT,OUT,sha

def main():
 manifest_path=OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
 assert manifest['original_inputs']==[]
 for path,digest in manifest['sources'].items():assert sha(ROOT/path)==digest,path
 for path,digest in manifest['generated'].items():assert sha(OUT/path)==digest,path
 assert sha(OUT/'OWNER.EXE')==manifest['binary_sha256']
 previous=[p for p in OUT.glob('dos-run-*') if p.is_dir()];run=OUT/('dos-run-'+str(len(previous)+1).zfill(3));run.mkdir(exist_ok=False)
 for leaf in ['OWNER.EXE','owner_host.c','owner_probe.asm']:(run/leaf).write_bytes((OUT/leaf).read_bytes())
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(run)+'"\nc:\nOWNER.EXE\nif errorlevel 1 goto BAD\necho PASS>PASS.TXT\ngoto DONE\n:BAD\necho FAIL>FAIL.TXT\n:DONE\nexit\n'
 (run/'dosbox.conf').write_text(config)
 with (run/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],cwd=run,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
 text=(run/'RESULT.TXT').read_text() if (run/'RESULT.TXT').exists() else ''
 matched=re.fullmatch(r'FIND_OWNER (\d+) checks (\d+) failures (\d+) operations\s*',text)
 checks=dict(DOS_exit=result.returncode==0 and (run/'PASS.TXT').exists() and not (run/'FAIL.TXT').exists(),
             summary=bool(matched),zero_failures=bool(matched) and matched[2]=='0',
             meaningful_matrix=bool(matched) and int(matched[1])>100000 and int(matched[3])>1000,
             binary_unchanged=sha(OUT/'OWNER.EXE')==manifest['binary_sha256'])
 report=dict(passed=all(checks.values()),checks=checks,DOS_summary=text.strip(),
             manifest_sha256=sha(manifest_path),checker_sha256=sha(Path(__file__)),binary_sha256=manifest['binary_sha256'],
             original_inputs=[],run_directory=str(run.relative_to(ROOT)),
             counts={'sizes':81,'IF_states':2,'allocation_failure_positions':2,'reuse_cycles':100},
             evidence_sha256={str(p.relative_to(ROOT)):sha(p) for p in [run/'dosbox.conf',run/'dosbox.log',run/'RESULT.TXT'] if p.exists()},
             scope=manifest['scope'],limitations=[
              'ActualDOSnearheap and maintained Cowner; runtime_set_error only recordsfirsttypederror.',
              'ProductionASM abort before nativeNULL dereference and wholeVMunwind are separate composition tests.',
              'Failurepositions are explicit diagnostic injections, not physicalmemoryexhaustion.',
              'C/CRT requiresDF0; IF0/1 preservation tested on warmnearheap, not arbitraryDOSallocation calls orIRQtiming.',
             ])
 (run/'checks.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print(text.strip() or 'FIND_OWNER no summary', 'PASS' if report['passed'] else 'FAIL')
 assert report['passed'],checks

if __name__=='__main__':main()
