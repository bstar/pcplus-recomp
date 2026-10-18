#!/usr/bin/env python3
"""Source-only maintained read-only DOS upload source and deterministic faults."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/upload-file';OUT.mkdir(parents=True,exist_ok=True);SRC=ROOT/'src/transfer'
sources=[SRC/'upload_file.c',SRC/'upload_fs.c',ROOT/'standalone/upload_file_normal.c',ROOT/'standalone/upload_file_fault.c']
for name,units in [('UPLOAD.EXE',[sources[0],sources[1],sources[2]]),('UPFAULT.EXE',[sources[0],sources[3]])]:
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(SRC),'-fm='+name.lower().replace('.exe','.map'),'-fe='+name,*map(str,units)],cwd=OUT,check=True)
(OUT/'SAMPLE.BIN').write_bytes(bytes((i*37+13)%256 for i in range(70013)));(OUT/'EMPTY.BIN').write_bytes(b'');(OUT/'SUBDIR').mkdir(exist_ok=True)
m={'kind':'maintained-readonly-upload-source-DOS-and-fault-diagnostics','outputs':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['UPLOAD.EXE','UPFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[SRC/'upload_file.h',SRC/'upload_fs.h']},'limitations':['Read-only DOS backend and mocked DOS failures; not a live sender/session/peer test.','Initial length snapshot only; concurrent equal-length content replacement is not detected.','Tokens1/2 are scoped to one foreground session, not generation-tagged across sessions.']};(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m['outputs'],indent=2))
