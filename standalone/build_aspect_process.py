#!/usr/bin/env python3
"""Build experimental full-VM external commands; do not replace shipped ASPECT."""
import json,subprocess
from pathlib import Path
import build_native_program as program
import build_aspect_runner as runner
ROOT=program.ROOT;OUT=ROOT/'build/aspect-process';sha=program.sha


def main(driver=None,parent_render=False):
    output=ROOT/'build/aspect-process-parent' if parent_render else OUT
    program.main();output.mkdir(parents=True,exist_ok=True)
    native=program.display.process
    process=json.loads((native.OUT/'manifest.json').read_text())
    display=json.loads((program.display.OUT/'manifest.json').read_text())
    ui=json.loads((ROOT/'reconstruction/program_ui/provenance.json').read_text())
    manifest=json.loads((program.OUT/'manifest.json').read_text())
    # Reuse the runtime's existing exact string/error routines and shared path
    # state. The variant widens DOS errno storage before exposing its WORD alias.
    reused={'strcpy','strlen','strncmp','strcmpi','error_exec','error_access','map_error','error_lookup'}
    objects=[str(native.OUT/(Path(u['file']).stem+'.obj')) for u in process['units'] if Path(u['file']).stem not in reused]
    objects += [str(program.display.OUT/(Path(u['file']).stem+'.obj')) for u in display['units']]
    objects += [str(program.OUT/(Path(u['file']).stem+'.obj')) for u in ui['units']]
    objects += [str(program.display.OUT/'display_state.obj'),str(program.OUT/'program_ui.obj')]
    state=ROOT/'src/process/native_process_state.asm';obj=output/'native_process_state.obj'
    subprocess.run(['nasm','-fobj','-DNATIVE_PROCESS_SHARED_PATH',str(state),'-o',str(obj)],check=True);objects.append(str(obj))
    c_sources=[ROOT/p for p in ('src/process/native_process.c','src/process/native_display.c',
        'src/process/native_program.c','src/aspect/process_serial.c','src/process/process_handles.c','src/aspect/external_runtime.c')]
    sources=[ROOT/name for name in manifest['sources']]
    sources += c_sources+[ROOT/'src/process/process_handles.h',ROOT/'src/aspect/external_runtime.h',Path(__file__)]
    extension=dict(output=output,objects=objects,c_sources=c_sources,sources=sources,parent_render=parent_render)
    if driver:extension['driver']=driver;extension['sources'].append(driver)
    runner.main(extension)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent-render',action='store_true')
    main(parent_render=parser.parse_args().parent_render)
