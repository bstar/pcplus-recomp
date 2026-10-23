#!/usr/bin/env python3
"""Exercise speaker policy boundaries with explicitly modeled clock/context/ports."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/speaker'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-D__cdecl=','-I'+str(ROOT/'src/ui'),str(ROOT/'src/ui/speaker.c'),str(ROOT/'standalone/speaker_host.c'),'-o',str(OUT/'host-check')],check=True)
    result=subprocess.run([str(OUT/'host-check')],capture_output=True,text=True)
    (OUT/'host-output.txt').write_text(result.stdout);m=re.fullmatch(r'SPEAKER HOST (\d+) checks\n',result.stdout)
    checks=dict(exit=result.returncode==0,cases=bool(m) and int(m[1])==68)
    r=dict(passed=all(checks.values()),checks=checks,assertions=int(m[1]) if m else None,output=result.stdout,stderr=result.stderr,sources={n:sha(ROOT/n) for n in ['standalone/test_speaker_host.py','standalone/speaker_host.c','src/ui/speaker.c','src/ui/speaker.h']},scope=__doc__+' Host integer widths differ from DOS; linked8086 checks and actual DOS separately establish native hardware/bank behavior.')
    (OUT/'host-result.json').write_text(json.dumps(r,indent=2)+'\n');print(result.stdout,end='');return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
