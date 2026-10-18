#!/usr/bin/env python3
"""Build recovered scroll services without reading any original installation."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal-reset';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/terminal_reset/provenance.json').read_text())
for unit in proof['units']:
 dest=OUT/(Path(unit['file']).stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(dest)],check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==unit['sha256']
sources=[]
for module in ['screen', 'erase', 'scroll', 'text', 'cursor_shape', 'terminal_services', 'terminal_reset']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources+=[ROOT/'reconstruction/attributes/reset.asm',ROOT/'standalone/terminal_reset_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.parent.name+'-'+source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-D'+source.parent.name.upper()+'_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'terminal_reset.map'),'name',str(OUT/'RESET.EXE'),'file',','.join(map(str,objects))],check=True)
group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',(OUT/'terminal_reset.map').read_text(),re.M|re.I)
assert group and int(group[1],16)<65536,'Diagnostic DS=SS group exceeds near segment'
manifest={'kind':'source-only-recovered-terminal-reset-diagnostic','data_stack_bytes':int(group[1],16),'binary_sha256':hashlib.sha256((OUT/'RESET.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Actual native soft-reset stable geometry/status-hidden path; full profile reset and broad UI/far allocation have explicit boundaries.','Full parser/renderer integration remains separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'RESET.EXE',manifest['binary_sha256'])
