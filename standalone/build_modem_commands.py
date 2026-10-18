#!/usr/bin/env python3
"""Source-only87-byte exact recovery plus maintained bounded near-call wrapper."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/modem-commands';out.mkdir(parents=True,exist_ok=True)
module=ROOT/'reconstruction/modem_commands';proof=json.loads((module/'provenance.json').read_text());core=module/'expand.asm'
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(core),'-o',str(out/'baseline.bin')],check=True)
b=(out/'baseline.bin').read_bytes();r=proof['ranges'][0];assert len(b)==r['size'] and hashlib.sha256(b).hexdigest()==r['sha256']
sources=[core,module/'bounded.asm',ROOT/'standalone/modem_commands_host.asm'];objects=[]
for i,p in enumerate(sources):
 obj=out/f'unit{i}.obj';objects.append(str(obj));subprocess.run(['nasm','-f','obj','-DMODEM_COMMANDS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'modem_commands.map'),'name',str(out/'MODEMCMD.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-modem-command-expansion-diagnostic','binary_sha256':hashlib.sha256((out/'MODEMCMD.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[module/'provenance.json',ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Decoder and bounded wrapper only; no serial transmission, timing or complete modem subsystem.','Raw recovered near ABI remains unsafe for malformed input; caller should use bounded wrapper.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built MODEMCMD.EXE;87 exact baseline bytes')
