#!/usr/bin/env python3
"""Source-only DOS retained-context, changed-directory and accounting diagnostic."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-context';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['src/config/live_configuration.c','src/config/terminal_import.c','src/config/modem_import.c','src/config/prm_dos.c','src/directory/directory_live.c','src/directory/directory_dos.c','src/directory/directory_actions.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/directory_context_host.c']
asm=[ROOT/'reconstruction/directory_dial/bounded.asm',ROOT/'reconstruction/directory_accounting/patch.asm'];objects=[]
for i,p in enumerate(asm):
 obj=OUT/f'unit{i}.obj';objects.append(str(obj));subprocess.run(['nasm','-f','obj',str(p),'-o',str(obj)],check=True)
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-fm=context.map','-fe=CONTEXT.EXE',*[str(ROOT/p) for p in SOURCES],*objects],cwd=OUT,check=True)
inputs=[ROOT/p for p in SOURCES]+asm+[Path(__file__).resolve()]+list((ROOT/'src/config').glob('*.h'))+list((ROOT/'src/directory').glob('*.h'))
r={'kind':'source-built-DOS-retained-directory-context-diagnostic','binary_sha256':hashlib.sha256((OUT/'CONTEXT.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'scope':'Synthetic standalone DOS context/candidate/accounting composition; no original EXE/private data, live setup UI or UART handoff.'}
(OUT/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built CONTEXT.EXE',r['binary_sha256'])
