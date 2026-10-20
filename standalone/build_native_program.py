#!/usr/bin/env python3
"""Compose recovered PROGRAM display/process and maintained UART ownership."""
import argparse,json,subprocess
from pathlib import Path
import build_native_display as display
import build_process_serial as serial
ROOT=display.ROOT;OUT=ROOT/'build/native-program';sha=display.sha


def main(guarded=False):
    global OUT
    OUT=ROOT/('build/native-program-break' if guarded else 'build/native-program')
    display.main();serial.main();OUT.mkdir(parents=True,exist_ok=True)
    dm=json.loads((display.OUT/'manifest.json').read_text())
    sm=json.loads((serial.OUT/'manifest.json').read_text())
    proof=json.loads((ROOT/'reconstruction/program_ui/provenance.json').read_text())
    objects=[str(display.OUT/(Path(u['file']).stem+'.obj')) for u in dm['units']]
    objects.append(str(display.OUT/'display_state.obj'))
    pm=json.loads((display.process.OUT/'manifest.json').read_text())
    objects += [str(display.process.OUT/(Path(u['file']).stem+'.obj')) for u in pm['units']]
    objects.append(str(display.process.OUT/'native_process_state.obj'))
    objects += [str(serial.OUT/(n+'.obj')) for n in ('uart','api','serial_backend','process_serial')]
    sources={**dm['sources'],**sm['sources'],**pm['sources']}
    if guarded:
        import build_break_owner as breaker
        breaker.main()
        bm=json.loads((breaker.OUT/'manifest.json').read_text())
        sources.update(bm['sources'])
        objects += [str(breaker.OUT/(name+'.obj')) for name in ('install','restore','ignore','break_binding')]
    sources['reconstruction/program_ui/provenance.json']=sha(ROOT/'reconstruction/program_ui/provenance.json')
    for unit in proof['units']:
        path=ROOT/unit['file'];sources[unit['file']]=sha(path)
        binary=OUT/(path.stem+'.bin');obj=OUT/(path.stem+'.obj')
        include='-I'+str(ROOT/'reconstruction/uart')+'/'
        subprocess.run(['nasm','-fbin',include,str(path),'-o',str(binary)],check=True)
        assert binary.stat().st_size==unit['bytes'] and sha(binary)==unit['sha256']
        subprocess.run(['nasm','-fobj','-DPROGRAM_DISPLAY_OMF',include,str(path),'-o',str(obj)],check=True)
        objects.append(str(obj))
    path=ROOT/'src/process/program_ui.asm';sources[str(path.relative_to(ROOT))]=sha(path)
    obj=OUT/'program_ui.obj';subprocess.run(['nasm','-fobj',str(path),'-o',str(obj)],check=True);objects.append(str(obj))
    c_sources=[ROOT/p for p in ('src/process/native_program.c','src/process/native_display.c',
        'src/process/native_process.c','src/aspect/serial.c','src/aspect/process_serial.c',
        'standalone/native_program_diagnostic.c')]
    if guarded:c_sources.append(ROOT/'src/process/break_owner.c')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        *(['-DNATIVE_PROGRAM_BREAK_OWNER'] if guarded else []),
        '-DASPECT_EXTERNAL_PROCESS','-DNATIVE_PROCESS_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC',
        '-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/aspect'),
        '-fm=PROGRAM.map','-fe=PROGRAM.EXE',*[str(p) for p in c_sources],*objects],cwd=OUT,check=True)
    for p in [*c_sources,ROOT/'src/process/native_program.h',Path(__file__),ROOT/'standalone/native_program_child.asm']:
        sources[str(p.relative_to(ROOT))]=sha(p)
    children={}
    for port in (1,2):
        child=OUT/f'OWN{port}.COM'
        subprocess.run(['nasm','-fbin','-DCHILD_PORT='+str(port),
            *(['-DBREAK_OWNER_TEST'] if guarded else []),
            str(ROOT/'standalone/native_program_child.asm'),'-o',str(child)],check=True)
        children[child.name]=sha(child)
    report=dict(passed=True,original_inputs=[],binary_sha256=sha(OUT/'PROGRAM.EXE'),children=children,
        native_ui_bytes=sum(u['bytes'] for u in proof['units']),units=proof['units'],sources=sources,break_owner=guarded,
        scope='Composed DOS process/display/UART component. No ASPECT dispatch, renderer/VM/mouse ownership publication or physical modem claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built PROGRAM.EXE with real DOS EXEC, recovered UI and gated UART owner.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--break-owner',action='store_true')
    main(parser.parse_args().break_owner)
