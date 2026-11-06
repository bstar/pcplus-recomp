#!/usr/bin/env python3
"""Build the opt-in source-only Chat/Redisplay profile with pinned-shell tools."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 flags=json.loads(Path(__file__).with_name('chat_redisplay_profile.json').read_text())
 assert '--chat-redisplay' in flags and all(f.startswith('--') for f in flags)
 subprocess.run([sys.executable,str(ROOT/'standalone/build_terminal.py'),'--output-dir',str(out),*flags],cwd=ROOT,check=True)

if __name__=='__main__':main()
