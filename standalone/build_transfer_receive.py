#!/usr/bin/env python3
"""Source-only exact receiver fragments with bounded memory/UART diagnostic."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-receive';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_receive'
proof=json.loads((MODULE/'provenance.json').read_text())
for unit in proof['units']:
 output=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(output)],check=True);raw=output.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256']
objects=[];sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/'reconstruction/transfer_blocks'/n for n in ['crc_update.asm','crc_finish.asm','crc_table.asm']]+[ROOT/'standalone/transfer_receive_host.asm']
for path in sources:
 obj=OUT/(path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_RECEIVE_OMF','-DTRANSFER_BLOCKS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_receive_dos_test(void);int main(void){return transfer_receive_dos_test();}\n')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-fm=transfer_receive.map','-fe=RECEIVE.EXE',str(OUT/'main.c'),*objects],cwd=OUT,check=True)
result={'kind':'source-only-exact-receiver-fragments-memory-UART-fixture','binary_sha256':hashlib.sha256((OUT/'RECEIVE.EXE').read_bytes()).hexdigest(),'exact_receiver_bytes':sum(x['bytes'] for x in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['Explicit diagnostic boundaries for UART/time/UI; no live UART, file commit, batch metadata or full transfer session.']};(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built RECEIVE.EXE;',result['exact_receiver_bytes'],'exact recovered receiver bytes')
