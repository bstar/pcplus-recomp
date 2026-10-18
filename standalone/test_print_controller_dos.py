#!/usr/bin/env python3
"""Actual8086 DOS execution of source-only native printer memory-FILE diagnostic.

Never opens a physical printer or executes the original PCPlus application.
CRT/device/status calls inside PRINTCTL.EXE are explicit diagnostic boundaries.
Every run has its own retained folder, including unsuccessful runs.
"""
import argparse,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/print_controller/PRINTCTL.EXE';OUT=ROOT/'build/print-controller-dos'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label');p.add_argument('--sha256');p.add_argument('--timeout',type=int,default=20);a=p.parse_args()
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert not a.sha256 or a.sha256==digest,'Diagnostic hash differs from requested freeze'
 manifest_path=BINARY.parent/'manifest.json';manifest=json.loads(manifest_path.read_text());assert manifest['binary_sha256']==digest,'Diagnostic differs from source build manifest'
 label=a.label or 'run-'+str(time.time_ns());assert label.replace('-','').replace('_','').isalnum(),'Invalid owned run label'
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);output=OUT/label;output.mkdir(exist_ok=False)
  before_names={p.name for p in BINARY.parent.iterdir()};config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\nserial1=disabled\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{output}"\nd:\nC:\\PRINTCTL >OUTPUT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
  (output/'dosbox.conf').write_text(config);started=time.monotonic();timeout=False
  with (output/'dosbox.log').open('w') as log:
   try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf')],cwd=output,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=a.timeout).returncode
   except subprocess.TimeoutExpired:code=-1;timeout=True
  stdout=(output/'OUTPUT.TXT').read_bytes() if (output/'OUTPUT.TXT').exists() else b''
  checks=dict(DOS_normal_exit=code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists(),selfcheck_reported_pass=b'PRINTCTL PASS' in stdout,within_timeout=not timeout,diagnostic_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,build_directory_names_unchanged=before_names=={p.name for p in BINARY.parent.iterdir()},no_unexpected_fixture_files=not [p.name for p in output.iterdir() if p.name not in {'dosbox.conf','dosbox.log','OUTPUT.TXT','PASS.TXT','FAIL.TXT'}])
  result=dict(passed=all(checks.values()),checks=checks,returncode=code,seconds=round(time.monotonic()-started,3),binary_sha256=digest,run=str(output.relative_to(ROOT)),selfcheck_stdout=stdout.decode('ascii','replace'),build_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual8086 DOS source-built native dedicated-print controller selfcheck. Device open/putc/flush/close/status are declared memory-FILE fixtures; no physicalPRN, serial modem, actual printerdriver errors or live dedicated printing claim.')
  result['artifacts']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
  (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True);return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
