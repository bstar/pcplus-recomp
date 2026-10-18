#!/usr/bin/env python3
"""Source-only recovered CRT and receiver file-commit diagnostic."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-files';OUT.mkdir(parents=True,exist_ok=True);MODULE=ROOT/'reconstruction/transfer_files'
proof=json.loads((MODULE/'provenance.json').read_text())
for unit in proof['units']:
 output=OUT/(Path(unit['source']).stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(MODULE/unit['source']),'-o',str(output)],check=True);raw=output.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256']
objects=[];sources=[MODULE/u['source'] for u in proof['units']]+[ROOT/'reconstruction/program_exec'/n for n in ['map_error.asm','error_lookup.asm']]+[ROOT/'standalone/transfer_files_host.asm'];exports=set();imports=set()
for path in sources:
 s=path.read_text();exports.update(n.strip() for line in re.findall(r'^global (.*)',s,re.M) for n in line.split(','));imports.update(re.findall(r'^extern (\w+)',s,re.M))
missing=sorted(imports-exports);(OUT/'boundaries.asm').write_text('BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\n'+'\n'.join('global '+n+'\n'+n+': int3\n ret' for n in missing)+'\n');sources.append(OUT/'boundaries.asm')
for i,path in enumerate(sources):
 obj=OUT/f'unit{i}.obj';objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_FILES_OMF','-DPROGRAM_EXEC_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','start=start','option','map='+str(OUT/'transfer_files.map'),'name',str(OUT/'FILES.EXE'),'file',','.join(objects)],cwd=OUT,check=True)
result={'kind':'source-only-native-CRT-write-flush-close-and-receiver-commit-diagnostic','binary_sha256':hashlib.sha256((OUT/'FILES.EXE').read_bytes()).hexdigest(),'exact_file_code_bytes':sum(x['bytes'] for x in proof['units']),'unresolved_traps':missing,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':proof['limitations']};(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built FILES.EXE;',result['exact_file_code_bytes'],'exact native bytes; unresolved:',','.join(missing))
