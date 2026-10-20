#!/usr/bin/env python3
"""Source-only native screen services and actual DOS/child diagnostic."""
import json,subprocess
from pathlib import Path
import build_native_process as process
ROOT=process.ROOT;OUT=ROOT/'build/native-display';CORE=ROOT/'reconstruction/program_display'
sha=process.sha


def main():
    process.main();OUT.mkdir(parents=True,exist_ok=True)
    proof=json.loads((CORE/'provenance.json').read_text());objects=[]
    sources=[Path(__file__),CORE/'provenance.json',ROOT/'reconstruction/uart/encodings.inc']
    for unit in proof['units']:
        p=ROOT/unit['file'];sources.append(p);flat=OUT/(p.stem+'.bin');obj=OUT/(p.stem+'.obj')
        include='-I'+str(ROOT/'reconstruction/uart')+'/'
        subprocess.run(['nasm','-fbin',include,str(p),'-o',str(flat)],check=True)
        assert flat.stat().st_size==unit['bytes'] and sha(flat)==unit['sha256']
        subprocess.run(['nasm','-fobj','-DPROGRAM_DISPLAY_OMF',include,str(p),'-o',str(obj)],check=True);objects.append(str(obj))
    state=ROOT/'src/process/native_display_state.asm';sources.append(state);obj=OUT/'display_state.obj'
    subprocess.run(['nasm','-fobj',str(state),'-o',str(obj)],check=True);objects.append(str(obj))
    manifest=json.loads((process.OUT/'manifest.json').read_text())
    # Link recovered process objects and real C environment/heap/trap owner.
    objects += [str(process.OUT/(Path(u['file']).stem+'.obj')) for u in manifest['units']]
    objects.append(str(process.OUT/'native_process_state.obj'))
    c_sources=[ROOT/'src/process/native_display.c',ROOT/'src/process/native_process.c',ROOT/'standalone/native_display_diagnostic.c']
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-DNATIVE_PROCESS_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC','-i='+str(ROOT/'src/process'),
        '-fm=DISPLAY.map','-fe=DISPLAY.EXE',*[str(p) for p in c_sources],*objects],cwd=OUT,check=True)
    child=ROOT/'standalone/native_display_child.asm';sources+=c_sources+[child,ROOT/'src/process/native_display.h']
    subprocess.run(['nasm','-fbin',str(child),'-o',str(OUT/'VIDEO.COM')],check=True)
    report=dict(passed=True,original_inputs=[],native_display_bytes=sum(u['bytes'] for u in proof['units']),
        units=proof['units'],binary_sha256=sha(OUT/'DISPLAY.EXE'),child_sha256=sha(OUT/'VIDEO.COM'),
        process_manifest_sha256=sha(process.OUT/'manifest.json'),process_sources=manifest['sources'],
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        limitations=proof['limitations'],scope='Native geometry/snapshot/restore with real far heap and a DOS graphics-mode child. Component only; no full PROGRAM controller or UART handoff.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built DISPLAY.EXE:',report['native_display_bytes'],'exact display bytes plus real process backend.')


if __name__=='__main__':main()
