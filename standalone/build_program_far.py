#!/usr/bin/env python3
"""Build a real UART/display/EXEC diagnostic across forced code-segment boundaries."""
import json,re,subprocess
from pathlib import Path
import build_native_program as program
import build_break_owner as breaker

ROOT=program.ROOT;OUT=ROOT/'build/native-program-far';sha=program.sha

def main():
    program.main(guarded=True);breaker.main(banked=True)
    OUT.mkdir(parents=True,exist_ok=True)
    pm=json.loads((program.OUT/'manifest.json').read_text())
    bm=json.loads((breaker.OUT/'manifest.json').read_text())
    dm=json.loads((program.display.OUT/'manifest.json').read_text())
    nm=json.loads((program.display.process.OUT/'manifest.json').read_text())
    proof=json.loads((ROOT/'reconstruction/program_ui/provenance.json').read_text())
    objects=[str(program.display.OUT/(Path(u['file']).stem+'.obj')) for u in dm['units']]
    objects.append(str(program.display.OUT/'display_state.obj'))
    objects += [str(program.display.process.OUT/(Path(u['file']).stem+'.obj')) for u in nm['units']]
    objects.append(str(program.display.process.OUT/'native_process_state.obj'))
    objects += [str(program.serial.OUT/(n+'.obj')) for n in ['uart','api','serial_backend','process_serial']]
    objects += [str(program.OUT/(Path(u['file']).stem+'.obj')) for u in proof['units']]
    objects += [str(breaker.OUT/(n+'.obj')) for n in ['install','restore','ignore','break_binding','break_owner_far']]
    ui=OUT/'program_ui_bank.obj'
    subprocess.run(['nasm','-fobj','-DNATIVE_PROGRAM_FAR',str(ROOT/'src/process/program_ui.asm'),'-o',str(ui)],check=True)
    objects.append(str(ui))
    flags=['-DASPECT_EXTERNAL_PROCESS','-DNATIVE_PROCESS_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC',
           '-DNATIVE_PROGRAM_BREAK_OWNER','-DNATIVE_BREAK_FAR','-DNATIVE_PROGRAM_FAR']
    include=['-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/aspect')]
    controller=OUT/'native_program_far.obj'
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',
        *flags,*include,'-nt=PROGRAMCODE','-fo='+str(controller),str(ROOT/'src/process/native_program.c')],cwd=OUT,check=True)
    objects.append(str(controller))
    c=[ROOT/name for name in ['src/process/native_process.c','src/process/native_display.c',
       'src/aspect/serial.c','src/aspect/process_serial.c','src/process/program_bank.c',
       'standalone/native_program_diagnostic.c']]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        *flags,*include,'-fd=PROGRAM.lnk','-fm=PROGRAM.map','-fe=PROGRAM.EXE',
        *map(str,c),*objects],cwd=OUT,check=True)
    with (OUT/'PROGRAM.lnk').open('a') as f:f.write('\noption packcode=0\n')
    subprocess.run(['wlink','@'+str(OUT/'PROGRAM.lnk')],cwd=OUT,check=True)
    listing=(OUT/'PROGRAM.map').read_text()
    segments={name:int(seg,16) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',listing,re.M|re.I)}
    assert segments['_native_program_execute']!=segments['main_']
    assert segments['_native_break_open']!=segments['main_']
    assert segments['program_break_ignore']==segments['program_break_install']
    sources={**pm['sources'],**bm['sources']}
    for path in [*c,ROOT/'src/process/program_bank.h',Path(__file__)]:sources[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in pm['children'].items():
        data=(program.OUT/name).read_bytes();(OUT/name).write_bytes(data);assert sha(OUT/name)==digest
    report=dict(passed=True,banked=True,break_owner=True,original_inputs=[],sources=sources,
        binary_sha256=sha(OUT/'PROGRAM.EXE'),children=pm['children'],
        scope='Real DOS EXEC/display/UART diagnostic with separate PROGRAM and break code segments; no VM fault instrumentation, physical modem or normal application publication.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built PROGRAM.EXE with forced far owner/controller and real platform adapters')

if __name__=='__main__':main()
