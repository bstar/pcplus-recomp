#!/usr/bin/env python3
"""Source-only diagnostic external-PCHELP placement control; never package it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from build_keymap_helper import ROOT,SOURCES

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper-build',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();base=args.helper_build.resolve();out=args.output.resolve()
    assert base.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    proof=json.loads((base/'result.json').read_text())
    assert proof['passed'] and proof['original_inputs']==[] and sha(base/'PCKEYMAP.EXE')==proof['binary_sha256']
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==digest,name
    compiled=[name for name in SOURCES if not name.startswith('src/help/') and name!='src/key_mapping/keymap_help.c']+['standalone/keymap_help_exec_control.c']
    names=sorted(set(compiled)|{name for name in proof['sources'] if not name.endswith('.c')}|{'standalone/build_keymap_help_exec_control.py'})
    out.mkdir(parents=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we','-k4096','-fm=PCKEYMAP.map','-fe=PCKEYMAP.EXE',*[str(ROOT/name) for name in compiled]],cwd=out,check=True)
    result=dict(passed=True,diagnostic_build=True,original_inputs=[],binary_sha256=sha(out/'PCKEYMAP.EXE'),sources={name:sha(ROOT/name) for name in names},scope=__doc__+' Current mapper/checked storage and descriptor17, with source PCHELP launched as an extra DOS process; full embedded viewer omitted. Compare real kernel EXEC results and later input/file preservation, not proprietary code or physical memory limits.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
