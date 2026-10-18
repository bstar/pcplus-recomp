#!/usr/bin/env python3
"""Source-only original sender/delays linked to the actual recovered UART."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/modem-send';OUT.mkdir(parents=True,exist_ok=True)
module=ROOT/'reconstruction/modem_send';proof=json.loads((module/'provenance.json').read_text())
for n,r in enumerate(proof['ranges']):
 p=OUT/f'baseline{n}.bin';subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(module/r['source']),'-o',str(p)],check=True);b=p.read_bytes();assert len(b)==r['size'] and hashlib.sha256(b).hexdigest()==r['sha256']
sources=[(module/r['source'],'MODEM_SEND_OMF') for r in proof['ranges']]+[(ROOT/'reconstruction/modem_commands/expand.asm','MODEM_COMMANDS_OMF'),(ROOT/'reconstruction/uart/core.asm','UART_OMF'),(ROOT/'standalone/data.asm',None),(ROOT/'standalone/modem_send_host.asm',None)];objects=[]
for n,(p,define) in enumerate(sources):
 o=OUT/f'unit{n}.obj';objects.append(str(o));subprocess.run(['nasm','-fobj',*(['-D'+define] if define else []),'-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(o)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'modem_send.map'),'name',str(OUT/'MODEMSND.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-modem-sender-with-real-uart','binary_sha256':hashlib.sha256((OUT/'MODEMSND.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [x[0] for x in sources]+[module/'provenance.json',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc']},'limitations':['Original sender is blocking with no intrinsic cancellation/deadline; safe compile-time command only.','Actual UART is linked. Fixed NO FLOW avoids unsupported application presentation services, which trap.','Echo is maintained BIOS diagnostic teletype; original0610 rendering remains external.','Fixture calibrated-loop values are synthetic, with no physical pacing-time claim.']};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built MODEMSND.EXE;172 exact sender/delay baseline bytes')
