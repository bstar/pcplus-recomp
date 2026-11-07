#!/usr/bin/env python3
"""Build the opt-in Alt-P parent; no release selection or physical deployment."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--overlay',action='store_true',help='Experimental transient code bank; no release/deployment selection')
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 flags=json.loads((ROOT/'standalone/line_port_profile.json').read_text())
 if a.overlay:flags.append('--line-port-overlay')
 subprocess.run([sys.executable,str(ROOT/'standalone/build_terminal.py'),*flags,'--output-dir',str(out)],cwd=ROOT,check=True)
 print('Experimental parent:',out/'TERMINAL.EXE','; installed release unchanged')


if __name__=='__main__':main()
