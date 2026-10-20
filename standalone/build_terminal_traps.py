#!/usr/bin/env python3
"""Build guarded application trap owners and explicitly named event probes."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    for mouse in [False,True]:
        flags=['--external-render','--exit-guard','--process-bank','--traps']+(['--mouse'] if mouse else [])
        for mode in [None,0,1,2,3,4]:
            subprocess.run([sys.executable,'standalone/build_terminal.py',*flags,*(['--trap-probe',str(mode)] if mode is not None else [])],cwd=ROOT,check=True)
if __name__=='__main__':main()
