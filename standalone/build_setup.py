#!/usr/bin/env python3
"""Source-only offline DOS configuration editor; no original PCSETUP input."""
from pathlib import Path
import argparse
import hashlib,json,subprocess
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mouse',action='store_true');parser.add_argument('--notice-sound',action='store_true');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/('build/setup-mouse-notice-sound' if args.notice_sound and args.mouse else 'build/setup-notice-sound' if args.notice_sound else 'build/setup-mouse' if args.mouse else 'build/setup');OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['setup_main.c','setup_document.c','setup_model.c','transfer_import.c','terminal_import.c','modem_import.c','prm_dos.c','prm_replace.c','prm_replace_fs.c']
sources=[ROOT/'src/config'/p for p in SOURCES]
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k16384',*(['-dSETUP_MOUSE'] if args.mouse else []),*(['-dSETUP_SOUND'] if args.notice_sound else []),'-i='+str(ROOT/'src/config'),'-fm=setup.map','-fe=PRMEDIT.EXE',*map(str,sources)],cwd=OUT,check=True)
sources+=list((ROOT/'src/config').glob('*.h'))+[Path(__file__).resolve()]
result={'kind':'source-built-offline-mapped-configuration-editor','experimental_mouse':args.mouse,'field_count':(50 if args.mouse else 48)+int(args.notice_sound),'experimental_notice_sound':args.notice_sound,'binary_sha256':hashlib.sha256((OUT/'PRMEDIT.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['Existing externally identified 2.01 image required; no version signature/default constructor.','Mapped fields only; original PCSETUP parent memory protocol not implemented.','Current-directory ASCII8.3 names only; no UART ownership or live parent changes.','Checked replacement and baseline comparison are not a writer lock or crash-atomic commit.']}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built PRMEDIT.EXE',result['binary_sha256'])
