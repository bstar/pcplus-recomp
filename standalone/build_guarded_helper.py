#!/usr/bin/env python3
"""Build the full helper terminal with owned traps and final-exit protection."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FLAGS='--external-render --mouse --notice-sound --notice-input --aspect-keys --directory-keys --process-bank --session-capture --session-projection --session-baseline --register-handoff --session-controls --hook-return --hook-execute --hook-modem --hook-input --hook-apply'.split()
CONTROL='terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply'
GUARDED=CONTROL+'-guarded-traps'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--probes',action='store_true');p.add_argument('--controls',action='store_true');a=p.parse_args()
 variants=([[]] if a.controls else [])+[['--exit-guard','--traps']]
 if a.probes:variants += [['--exit-guard','--traps','--trap-probe',str(i)]for i in range(5)]
 for flags in variants:subprocess.run([sys.executable,'standalone/build_terminal.py',*FLAGS,*flags],cwd=ROOT,check=True)
if __name__=='__main__':main()
