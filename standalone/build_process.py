#!/usr/bin/env python3
"""Build maintained bounded EXEC and synthetic DOS child without vendor files."""
import hashlib,json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/process';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/process/dos_exec.asm',ROOT/'standalone/process_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'process.map'),'name',str(OUT/'PROCESS.EXE'),'file',','.join(map(str,objects))],check=True)
child=ROOT/'standalone/process_child.asm';sources.append(child)
subprocess.run(['nasm','-f','bin',str(child),'-o',str(OUT/'CHILD.COM')],check=True)
program=ROOT/'src/process/program.c';host=ROOT/'standalone/program_host.asm';sources += [program,host,ROOT/'src/process/dos_exec.h']
subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/process'),'-fo='+str(OUT/'program.obj'),str(program)],cwd=OUT,check=True)
subprocess.run(['nasm','-f','obj',str(host),'-o',str(OUT/'program_host.obj')],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'program.map'),'name',str(OUT/'PROGRAM.EXE'),'file',','.join(str(OUT/name) for name in ['dos_exec.obj','program.obj','program_host.obj']),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
manifest={'kind':'maintained-bounded-DOS-EXEC-diagnostic','sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'PROCESS.EXE',OUT/'CHILD.COM',OUT/'PROGRAM.EXE']},'scope':'Generic maintained DOS EXEC boundary, static-parent resize and bounded COMSPEC/PATH policy. Native vendor program dispatch/executor recovery is separate. Synthetic diagnostic child only; no live UART handoff yet.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built PROCESS.EXE, PROGRAM.EXE and synthetic CHILD.COM',manifest['outputs'])
