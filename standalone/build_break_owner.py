#!/usr/bin/env python3
"""Build guarded native break ownership with the recovered DOS EXEC backend."""
from pathlib import Path
import json
import subprocess
import build_native_process as process

ROOT=process.ROOT;OUT=ROOT/'build/break-owner';sha=process.sha
def main():
    process.main();OUT.mkdir(parents=True,exist_ok=True)
    pm=json.loads((process.OUT/'manifest.json').read_text())
    objects=[str(process.OUT/(Path(u['file']).stem+'.obj')) for u in pm['units']]
    objects.append(str(process.OUT/'native_process_state.obj'))
    sources=dict(pm['sources']);core=ROOT/'reconstruction/program_break'
    proof=json.loads((core/'provenance.json').read_text())
    for unit in proof['units']:
        source=ROOT/unit['file'];binary=OUT/(source.stem+'.bin');obj=OUT/(source.stem+'.obj')
        include=['-I',str(core)+'/', '-I',str(ROOT/'reconstruction/uart')+'/']
        subprocess.run(['nasm','-fbin',*include,str(source),'-o',str(binary)],check=True)
        assert sha(binary)==unit['sha256']
        subprocess.run(['nasm','-fobj','-DPROGRAM_BREAK_OMF',*include,str(source),'-o',str(obj)],check=True)
        objects.append(str(obj));sources[unit['file']]=sha(source)
    assembly=ROOT/'src/process/break_owner.asm';obj=OUT/'break_binding.obj'
    subprocess.run(['nasm','-fobj',str(assembly),'-o',str(obj)],check=True);objects.append(str(obj))
    c=[ROOT/name for name in ('src/process/native_process.c','src/process/break_owner.c','standalone/break_owner_diagnostic.c')]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-DNATIVE_PROCESS_DIAGNOSTIC','-i='+str(ROOT/'src/process'),'-fm=BRKOWN.map','-fe=BRKOWN.EXE',
        *[str(p) for p in c],*objects],cwd=OUT,check=True)
    child=ROOT/'standalone/break_owner_child.asm'
    subprocess.run(['nasm','-fbin',str(child),'-o',str(OUT/'BRKCHLD.COM')],check=True)
    for source in [*c,assembly,child,core/'abi.inc',core/'provenance.json',ROOT/'src/process/break_owner.h',Path(__file__)]:
        sources[str(source.relative_to(ROOT))]=sha(source)
    (OUT/'manifest.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(OUT/'BRKOWN.EXE'),
        child_sha256=sha(OUT/'BRKCHLD.COM'),sources=sources,original_inputs=[],
        scope='Guarded break owner with real recovered DOS process backend; separate diagnostic, not published PROGRAM/ASPECT.'),indent=2)+'\n')
    print('Built BRKOWN.EXE and independent BRKCHLD.COM')
if __name__=='__main__':main()
