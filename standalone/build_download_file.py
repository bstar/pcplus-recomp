#!/usr/bin/env python3
"""Build maintained streaming DOS file boundary and fault diagnostic."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/download-file';OUT.mkdir(parents=True,exist_ok=True)
common=[ROOT/'src/transfer/download_file.c',ROOT/'src/transfer/native_file_bridge.c']
normal=common+[ROOT/'src/transfer/download_fs.c',ROOT/'standalone/download_file_host.c']
fault=common+[ROOT/'standalone/download_file_faults.c']
base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/transfer')]
for name,sources in [('DOWNLOAD.EXE',normal),('DLFAULT.EXE',fault)]:
 subprocess.run(base+['-fe='+name]+list(map(str,sources)),cwd=OUT,check=True)
sources=set(normal+fault+[ROOT/'src/transfer/download_file.h',ROOT/'src/transfer/download_fs.h',ROOT/'src/transfer/native_file_bridge.h'])
manifest={'kind':'maintained-streaming-download-DOS-file-boundary','sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'binaries':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['DOWNLOAD.EXE','DLFAULT.EXE']},'scope':'Maintained exact-write/checked-close/no-overwrite download storage with explicit stage/handle recovery; diagnostic is separate from native CRT recovery and live UART/protocol session.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built streaming download and fault diagnostics',manifest['binaries'])
