#!/usr/bin/env python3
"""Build the popup transaction with native selector in its relocatable code bank."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-session';OUT.mkdir(parents=True,exist_ok=True)
for source,name in [('reconstruction/line_port/key.asm','key'),('src/line_port/select.asm','select')]:
 subprocess.run(['nasm','-fobj','-DLINE_PORT_OMF','-DLINE_PORT_FAR_BANK','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/source),'-o',str(OUT/(name+'.obj'))],check=True)
subprocess.run(['nasm','-fobj',str(ROOT/'standalone/line_port_bank_pad.asm'),'-o',str(OUT/'pad.obj')],check=True)
# Compile bank units separately so their near calls stay in the same bank.
for name in ('session','view','plan'):
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-nt=LINE_PORT_CODE','-nc=FARCODE','-fo='+str(OUT/(name+'.obj')),str(ROOT/'src/line_port'/(name+'.c'))],check=True)
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fd=SESSION.lnk','-fm=SESSION.map','-fe=SESSION.EXE',str(ROOT/'standalone/line_port_session_diagnostic.c'),'session.obj','view.obj','plan.obj','key.obj','select.obj','pad.obj'],cwd=OUT,check=True)
response=OUT/'SESSION.lnk'
response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname DATA clname BSS clname STACK\n')
subprocess.run(['wlink','@SESSION.lnk'],cwd=OUT,check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['reconstruction/line_port/key.asm','reconstruction/line_port/provenance.json','reconstruction/uart/encodings.inc','src/line_port/select.asm','src/line_port/session.c','src/line_port/session.h','src/line_port/view.c','src/line_port/view.h','src/line_port/plan.c','src/line_port/plan.h','src/config/terminal_import.h','src/config/prm_dos.h','standalone/line_port_session_diagnostic.c','standalone/build_line_port_session.py','standalone/line_port_bank_pad.asm']
(OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],binary_sha256=sha(OUT/'SESSION.EXE'),sources={n:sha(ROOT/n)for n in names},scope='Transaction/renderer plus exact native selector in LINE_PORT_CODE. Persistence and UART results are explicit authored inputs, not actual operations.'),indent=2)+'\n')
print('Built source-only popup session in separate LINE_PORT_CODE bank')
