#!/usr/bin/env python3
"""Build guarded native break ownership with the recovered DOS EXEC backend."""
from pathlib import Path
import argparse,json,re
import subprocess
import build_native_process as process

ROOT=process.ROOT;OUT=ROOT/'build/break-owner';sha=process.sha
def main(banked=False):
    global OUT
    OUT=ROOT/('build/break-owner-far' if banked else 'build/break-owner')
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
        subprocess.run(['nasm','-fobj','-DPROGRAM_BREAK_OMF',*(['-DNATIVE_BREAK_FAR'] if banked else []),*include,str(source),'-o',str(obj)],check=True)
        objects.append(str(obj));sources[unit['file']]=sha(source)
    assembly=ROOT/'src/process/break_owner.asm';obj=OUT/'break_binding.obj'
    subprocess.run(['nasm','-fobj',*(['-DNATIVE_BREAK_FAR'] if banked else []),str(assembly),'-o',str(obj)],check=True);objects.append(str(obj))
    c=[ROOT/name for name in ('src/process/native_process.c','src/process/break_owner.c','standalone/break_owner_diagnostic.c')]
    linked=list(c)
    link_flags=[]
    if banked:
        link_flags=['-fd=BRKOWN.lnk']
        owner=OUT/'break_owner_far.obj'
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-os','-ob','-w4','-we',
            '-DNATIVE_BREAK_FAR','-nt=BRKCODE','-fo='+str(owner),str(c[1])],cwd=OUT,check=True)
        linked.remove(c[1]);objects.append(str(owner))
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        *link_flags,
        *(['-DNATIVE_BREAK_FAR'] if banked else []),
        '-DNATIVE_PROCESS_DIAGNOSTIC','-i='+str(ROOT/'src/process'),'-fm=BRKOWN.map','-fe=BRKOWN.EXE',
        *[str(p) for p in linked],*objects],cwd=OUT,check=True)
    if banked:
        directives=OUT/'BRKOWN.lnk'
        with directives.open('a') as f:f.write('\noption packcode=0\n')
        subprocess.run(['wlink','@'+str(directives)],cwd=OUT,check=True)
        listing=(OUT/'BRKOWN.map').read_text()
        symbols={name:int(seg,16) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',listing,re.M|re.I)}
        bank=symbols['program_break_install']
        assert all(symbols[name]==bank for name in ('program_break_restore','program_break_ignore','_native_break_open','_native_break_handler'))
        assert bank!=symbols['main_'],'Diagnostic must exercise an actual CS boundary'
    child=ROOT/'standalone/break_owner_child.asm'
    subprocess.run(['nasm','-fbin',str(child),'-o',str(OUT/'BRKCHLD.COM')],check=True)
    for source in [*c,assembly,child,core/'abi.inc',core/'provenance.json',ROOT/'src/process/break_owner.h',Path(__file__)]:
        sources[str(source.relative_to(ROOT))]=sha(source)
    (OUT/'manifest.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(OUT/'BRKOWN.EXE'),
        child_sha256=sha(OUT/'BRKCHLD.COM'),sources=sources,original_inputs=[],banked=banked,
        scope='Guarded break owner with real recovered DOS process backend; separate diagnostic, not published PROGRAM/ASPECT.'),indent=2)+'\n')
    print('Built BRKOWN.EXE and independent BRKCHLD.COM')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--banked',action='store_true')
    main(parser.parse_args().banked)
