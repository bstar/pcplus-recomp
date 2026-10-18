#!/usr/bin/env python3
"""Source-only offline DOS configuration editor; no original PCSETUP input."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['setup_main.c','setup_document.c','setup_model.c','terminal_import.c','modem_import.c','prm_dos.c','prm_replace.c','prm_replace_fs.c']
sources=[ROOT/'src/config'/p for p in SOURCES]
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k16384','-i='+str(ROOT/'src/config'),'-fm=setup.map','-fe=PRMEDIT.EXE',*map(str,sources)],cwd=OUT,check=True)
sources+=list((ROOT/'src/config').glob('*.h'))+[Path(__file__).resolve()]
result={'kind':'source-built-offline-mapped-configuration-editor','binary_sha256':hashlib.sha256((OUT/'PRMEDIT.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['Existing externally identified 2.01 image required; no version signature/default constructor.','44 mapped fields only; original PCSETUP parent memory protocol not implemented.','Current-directory ASCII8.3 names only; no UART ownership or live parent changes.','Checked replacement and baseline comparison are not a writer lock or crash-atomic commit.']}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built PRMEDIT.EXE',result['binary_sha256'])
