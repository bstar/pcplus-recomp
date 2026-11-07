#!/usr/bin/env python3
"""Build the opt-in Alt-P parent; no release selection or physical deployment."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 flags=json.loads((ROOT/'standalone/line_port_profile.json').read_text())
 subprocess.run([sys.executable,str(ROOT/'standalone/build_terminal.py'),*flags,'--output-dir',str(out)],cwd=ROOT,check=True)
 print('Experimental parent:',out/'TERMINAL.EXE','; installed release unchanged')


if __name__=='__main__':main()
