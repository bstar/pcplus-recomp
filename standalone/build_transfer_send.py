#!/usr/bin/env python3
"""Source-only exact sender diagnostic with declared memory FILE/UART/UI fixtures."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-send';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_send'
p=json.loads((MODULE/'provenance.json').read_text());objects=[]
for unit in p['units']:
 out=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(out)],check=True)
 raw=out.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256']
sources=[MODULE/u['source'] for u in p['units']]+[ROOT/'reconstruction/transfer_blocks'/n for n in ['crc_update.asm','crc_finish.asm','crc_buffer.asm','crc_table.asm']]+[ROOT/'standalone/transfer_send_host.asm']
for path in sources:
 obj=OUT/(path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_SEND_OMF','-DTRANSFER_BLOCKS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_send_dos_test(void);int main(void){return transfer_send_dos_test();}\n')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=transfer_send.map','-fe=SEND.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
r={'binary_sha256':hashlib.sha256((OUT/'SEND.EXE').read_bytes()).hexdigest(),'exact_sender_bytes':sum(x['bytes'] for x in p['units']),'sources':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources},'limitations':['Declared memory FILE/UART/time/UI and alternate-protocol failure fixtures; no actual file IO, live UART, remotepeer or complete original UI.']};(OUT/'manifest.json').write_text(json.dumps(r,indent=2)+'\n');print('Built SEND.EXE',r['exact_sender_bytes'],'exactbytes')
