#!/usr/bin/env python3
"""Build only maintained popup rendering; no original or private inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-view'
OUT.mkdir(parents=True,exist_ok=True)
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096',
 '-fm=VIEW.map','-fe=VIEW.EXE',str(ROOT/'src/line_port/view.c'),
 str(ROOT/'standalone/line_port_view_diagnostic.c')],cwd=OUT,check=True)
names=['src/line_port/view.c','src/line_port/view.h','standalone/line_port_view_diagnostic.c','standalone/build_line_port_view.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],binary_sha256=sha(OUT/'VIEW.EXE'),
 sources={n:sha(ROOT/n)for n in names},scope='Maintained renderer diagnostic only; no live terminal/UART/file-settings integration.'),indent=2)+'\n')
print('Built source-only Line/Port popup renderer')
