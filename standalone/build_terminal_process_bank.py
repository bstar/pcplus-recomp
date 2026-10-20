#!/usr/bin/env python3
"""Build banked terminal execution and independently named DOS probes."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    for mouse in [False,True]:
        flags=['--external-render','--exit-guard','--process-bank']+(['--mouse'] if mouse else [])
        for mode in [None,0,1,2,3]:
            subprocess.run([sys.executable,'standalone/build_terminal.py',*flags,*(['--exit-probe',str(mode)] if mode is not None else [])],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'standalone/build_process.py','--banked'],cwd=ROOT,check=True)
if __name__=='__main__':main()
