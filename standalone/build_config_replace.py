#!/usr/bin/env python3
"""Build maintained DOS configuration replacement and fault regressions."""
from pathlib import Path
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/config-replace';OUT.mkdir(parents=True,exist_ok=True)
base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config')]
normal=[ROOT/p for p in ['src/config/prm_dos.c','src/config/prm_replace.c','src/config/prm_replace_fs.c','standalone/config_replace_host.c']]
subprocess.run(base+['-fe=REPLACE.EXE']+list(map(str,normal)),cwd=OUT,check=True)
fault=[ROOT/'src/config/prm_replace.c',ROOT/'standalone/config_replace_faults.c']
names={'_dos_getfileattr':'prm_fault_getfileattr','_dos_creatnew':'prm_fault_creatnew','_dos_write':'prm_fault_write','_dos_close':'prm_fault_close','prm_replace_rename':'prm_fault_rename','prm_replace_delete':'prm_fault_delete'}
subprocess.run(base+['-fe=REPFAULT.EXE']+['-d'+k+'='+v for k,v in names.items()]+list(map(str,fault)),cwd=OUT,check=True)
sources=set(normal+fault+[ROOT/'src/config/prm_dos.h',ROOT/'src/config/prm_replace.h',ROOT/'src/config/prm_replace_fs.h'])
manifest={'kind':'maintained-source-only-dos-config-replacement','binaries':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['REPLACE.EXE','REPFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'limitations':['Failure-aware staged replacement, not crash-atomic filesystem commit.','Distinct ASCII8.3 leaf names in current DOS directory only.','Caller must inspect installed/recovery flags after errors; recovery files are not automatically overwritten.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built configuration replacement diagnostics',manifest['binaries'])
