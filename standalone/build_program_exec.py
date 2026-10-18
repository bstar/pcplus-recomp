#!/usr/bin/env python3
"""Source-only original PROGRAM/CRT execution recovery plus explicit gaps."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'reconstruction/program_exec';OUT=ROOT/'build/program-exec';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((CORE/'provenance.json').read_text())
for unit in proof['units']:
 path=ROOT/unit['file'];target=OUT/(path.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(target)],check=True)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256'],path
sources=sorted(CORE.glob('*.asm'));globals_=set();externs=set()
for path in sources:
 text=path.read_text();externs.update(re.findall(r'^extern (\w+)',text,re.M))
 for names in re.findall(r'^global (.*)',text,re.M):globals_.update(names.split(','))
state={name:int(addr,16) for addr,name in proof['state'].items()}
lines=['SEGMENT _TEXT']
for name in sorted(externs-globals_):
 if name in state:continue
 lines+=['global '+name,name+':',' int3',' ret']
lines+=['SEGMENT _DATA public class=DATA use16','global program_state_base','program_state_base:']
for name,offset in sorted(state.items(),key=lambda p:p[1]):
 if name in globals_:continue
 lines+=['global '+name,name+f' equ program_state_base+0x{offset:x}']
lines+=[' times 0xe500 db 0']
(OUT/'program_state.inc').write_text('\n'.join(lines)+'\n');sources+=[ROOT/'standalone/program_exec_host.asm'];objects=[]
for i,path in enumerate(sources):
 obj=OUT/f'unit{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DPROGRAM_EXEC_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(OUT)+'/',str(path),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'program_exec.map'),'name',str(OUT/'EXECUTOR.EXE'),'file',','.join(objects)],check=True)
subprocess.run(['nasm','-f','bin','-DPROGRAM_EXEC_CHILD',str(ROOT/'standalone/program_exec_host.asm'),'-o',str(OUT/'CHILD.COM')],check=True)
manifest={'kind':'source-only-original-program-exec-diagnostic','binary_sha256':hashlib.sha256((OUT/'EXECUTOR.EXE').read_bytes()).hexdigest(),'child_sha256':hashlib.sha256((OUT/'CHILD.COM').read_bytes()).hexdigest(),'exact_recovered_bytes':sum(x['bytes'] for x in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'provenance.json']},'limitations':proof['limitations'],'DOS_diagnostic':'Original6a22 EXEC core, actual DOS4B00/4D, source-owned synthetic COM child; maintained diagnostic PSPshrink; no original code outside recovered source launched.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built EXECUTOR.EXE and owned CHILD.COM;',manifest['exact_recovered_bytes'],'exact recovered bytes')
