#!/usr/bin/env python3
"""Compile source-owned DOS config backend/tests through pinned Open Watcom."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/config-dos';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/config/prm_dos.c',ROOT/'standalone/config_dos_host.c']
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config'),'-fe=CONFIG.EXE',*map(str,sources)],cwd=OUT,check=True)
fault_source=ROOT/'standalone/config_dos_faults.c'
fault_options=['-d'+name+'=prm_fault_'+name[5:] for name in ['_dos_open','_dos_creat','_dos_close','_dos_read','_dos_write']]
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config'),'-fe=CFGFAULT.EXE',*fault_options,str(sources[0]),str(fault_source)],cwd=OUT,check=True)
sources.append(fault_source)
manifest={'kind':'maintained-source-only-dos-prm-io-diagnostic','binary_sha256':hashlib.sha256((OUT/'CONFIG.EXE').read_bytes()).hexdigest(),'fault_binary_sha256':hashlib.sha256((OUT/'CFGFAULT.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/config/prm_dos.h']},'limitations':['Maintained opaque1264-byte IO, not original recovered configuration routines or complete defaults/schema/UI.','Direct save reports failure but may leave destination truncated/partial; transactional replacement remains application work.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built CONFIG.EXE',manifest['binary_sha256'])
