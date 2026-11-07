#!/usr/bin/env python3
"""Reproduce the popup renderer from five public files in an empty tree."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-view'
DEST=OUT/'source-proof'
SOURCES=['src/line_port/view.c','src/line_port/view.h',
 'standalone/line_port_view_diagnostic.c','standalone/build_line_port_view.py',
 'standalone/test_line_port_view_dos.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 DEST.mkdir(parents=True,exist_ok=False)
 tree=DEST/'tree'
 for source in SOURCES:
  target=tree/source;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(ROOT/source,target)
 for command in ('build_line_port_view.py','test_line_port_view_dos.py'):
  subprocess.run([sys.executable,str(tree/'standalone'/command)],cwd=tree,check=True)
 names=['VIEW.EXE']+[f'dos/VIEW{i}.BIN'for i in range(3)]
 for name in names:assert (OUT/name).read_bytes()==(tree/'build/line-port-view'/name).read_bytes(),name
 (DEST/'result.json').write_text(json.dumps(dict(passed=True,
  sources={n:sha(ROOT/n)for n in SOURCES},exact_outputs={n:sha(OUT/n)for n in names},
  dos_result=json.loads((tree/'build/line-port-view/dos-results.json').read_text()),
  scope='Five public files, no original/configuration/analysis database/prior object/Git metadata. Outer pinned Nix environment supplies tools.'),indent=2)+'\n')
 print('Five-file renderer export reproduces EXE and all three DOS frames exactly')


if __name__=='__main__':main()
