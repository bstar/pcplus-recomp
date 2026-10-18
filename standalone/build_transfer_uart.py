#!/usr/bin/env python3
"""Reuse real UART core; add exact clocks/header timeout and bounded adapter."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-uart';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_uart';p=json.loads((MODULE/'provenance.json').read_text())
for i,u in enumerate(p['units']):
 out=OUT/(str(i)+'.bin');cmd=['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/']
 if u['region'] is not None:cmd+=['-DTRANSFER_UART_REGION='+str(u['region'])]
 subprocess.run(cmd+[str(MODULE/u['source']),'-o',str(out)],check=True);raw=out.read_bytes();assert len(raw)==u['bytes'] and hashlib.sha256(raw).hexdigest()==u['sha256']
sources=[ROOT/'reconstruction/uart/core.asm',ROOT/'standalone/data.asm',MODULE/'clock.asm',MODULE/'header_timeout.asm',MODULE/'bindings.asm',MODULE/'bounded.asm',ROOT/'standalone/transfer_uart_host.asm'];objects=[]
for i,path in enumerate(sources):
 obj=OUT/(str(i)+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DUART_OMF','-DTRANSFER_UART_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_uart_dos_test(void);int main(void){return transfer_uart_dos_test();}\n')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=transfer_uart.map','-fe=TUART.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
proof={'binary_sha256':hashlib.sha256((OUT/'TUART.EXE').read_bytes()).hexdigest(),'new_exact_bytes':sum(u['bytes'] for u in p['units']),'sources':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources},'limitations':['Reuse existing recovered UARTcore with maintained ISR safeguards; exact clocks/header, source-owned alias/extent adapter.','Diagnostic UI callbacks are explicit fixtures. No live application integration or physicaladapter proof.']};(OUT/'manifest.json').write_text(json.dumps(proof,indent=2)+'\n');print('Built TUART.EXE',proof['binary_sha256'])
