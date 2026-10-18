#!/usr/bin/env python3
"""Source-only original CRC and maintained bounded block framing diagnostic."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-blocks';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_blocks'
proof=json.loads((MODULE/'provenance.json').read_text())
for unit in proof['units']:
 output=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(output)],check=True);raw=output.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256']
output=OUT/'table.bin';subprocess.run(['nasm','-fbin',str(MODULE/'crc_table.asm'),'-o',str(output)],check=True);assert hashlib.sha256(output.read_bytes()).hexdigest()==proof['crc_table']['sha256']
objects=[];sources=sorted(MODULE.glob('*.asm'))+[ROOT/'standalone/transfer_blocks_host.asm']
for path in sources:
 obj=OUT/(path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_BLOCKS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_blocks_dos_test(void);int main(void){return transfer_blocks_dos_test();}\n')
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(MODULE),'-fm=transfer_blocks.map','-fe=BLOCKS.EXE',str(MODULE/'blocks.c'),str(OUT/'main.c'),*objects],cwd=OUT,check=True)
result={'kind':'source-only-original-CRC-and-maintained-bounded-block-framing','binary_sha256':hashlib.sha256((OUT/'BLOCKS.EXE').read_bytes()).hexdigest(),'exact_code_bytes':sum(x['bytes'] for x in proof['units']),'generated_verified_table_bytes':512,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[MODULE/'blocks.c',MODULE/'blocks.h',MODULE/'provenance.json']},'limitations':['Pure block encoding/CRC only, no live UART,file transfer, retries, UI or peer interop.']};(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built BLOCKS.EXE;',result['exact_code_bytes'],'exact CRC bytes +512 independently generated table')
