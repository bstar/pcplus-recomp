#!/usr/bin/env python3
"""Build the gated external UART owner with real DOS process and UART cores."""
import json,subprocess
from pathlib import Path
import build_native_process as process
ROOT=process.ROOT;OUT=ROOT/'build/process-serial';sha=process.sha


def main():
    process.main();OUT.mkdir(parents=True,exist_ok=True)
    sources=[Path(__file__)];objects=[]
    for name,rel,flags in [('uart','reconstruction/uart/core.asm',['-DUART_OMF']),
        ('api','src/uart/api.asm',[]),('serial_backend','src/aspect/serial_backend.asm',[]),
        ('process_serial','src/aspect/process_serial.asm',[])]:
        p=ROOT/rel;sources.append(p);obj=OUT/(name+'.obj')
        subprocess.run(['nasm','-fobj','-DASPECT_EXTERNAL_PROCESS',*flags,'-I'+str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(obj)],check=True)
        objects.append(str(obj))
    parent=json.loads((process.OUT/'manifest.json').read_text())
    objects += [str(process.OUT/(Path(u['file']).stem+'.obj')) for u in parent['units']]
    objects.append(str(process.OUT/'native_process_state.obj'))
    c_sources=[ROOT/'src/aspect/serial.c',ROOT/'src/aspect/process_serial.c',ROOT/'src/process/native_process.c',ROOT/'standalone/process_serial_diagnostic.c']
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-DASPECT_EXTERNAL_PROCESS','-DNATIVE_PROCESS_DIAGNOSTIC','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'src/process'),
        '-fm=process_serial.map','-fe=PSERIAL.EXE',*[str(p) for p in c_sources],*objects],cwd=OUT,check=True)
    sources+=c_sources+[ROOT/'src/aspect/process_serial.h',ROOT/'src/aspect/serial.h',ROOT/'src/aspect/serial_handoff.h',
        ROOT/'src/aspect/resident_render.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',
        ROOT/'reconstruction/directory_accounting/patch.asm',ROOT/'standalone/process_serial_child.asm']
    children={}
    for port in (1,2):
        p=OUT/f'UART{port}.COM'
        subprocess.run(['nasm','-fbin','-DCHILD_PORT='+str(port),str(ROOT/'standalone/process_serial_child.asm'),'-o',str(p)],check=True)
        children[p.name]=sha(p)
    report=dict(passed=True,original_inputs=[],binary_sha256=sha(OUT/'PSERIAL.EXE'),children=children,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},process_sources=parent['sources'],
        process_manifest_sha256=sha(process.OUT/'manifest.json'),
        scope='Gated external-process UART owner; original bounded UART/ISR and real native DOS EXEC. No display/ASPECT runtime publication or physical modem claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built PSERIAL.EXE and owned COM1/COM2 port-mutating children.')


if __name__=='__main__':main()
