#!/usr/bin/env python3
"""Source-only DOS candidate decoder diagnostic; no active hardware changes."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/live-configuration';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['src/config/live_configuration.c','src/config/terminal_import.c','src/config/modem_import.c','src/config/prm_dos.c','src/directory/directory_live.c','src/directory/directory_dos.c','standalone/live_configuration_host.c']
number=ROOT/'reconstruction/directory_dial/bounded.asm';obj=OUT/'number.obj'
subprocess.run(['nasm','-f','obj',str(number),'-o',str(obj)],check=True)
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k16384','-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-fm=live.map','-fe=LIVE.EXE',*map(str,[ROOT/p for p in SOURCES]),str(obj)],cwd=OUT,check=True)
inputs=[ROOT/p for p in SOURCES]+[number,Path(__file__).resolve()]+list((ROOT/'src/config').glob('*.h'))+list((ROOT/'src/directory').glob('*.h'))
r={'kind':'source-built-pure-live-configuration-candidate-diagnostic','binary_sha256':hashlib.sha256((OUT/'LIVE.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Candidate decoder only; not yet a live setup UI or UART/profile handoff.','Directory read and pure decode share validation; raw/global serial validation still precedes per-entry overrides.','Unknown PRM bytes are not applied; DIRECT retains the existing modem-skip policy.']}
(OUT/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built LIVE.EXE',r['binary_sha256'])
