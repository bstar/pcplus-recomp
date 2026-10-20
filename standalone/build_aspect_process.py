#!/usr/bin/env python3
"""Build experimental full-VM external commands; do not replace shipped ASPECT."""
import json,subprocess
from pathlib import Path
import build_native_program as program
import build_aspect_runner as runner
ROOT=program.ROOT;OUT=ROOT/'build/aspect-process';sha=program.sha


def main(driver=None,parent_render=False,output=None,break_owner=False):
    if output is None:output=ROOT/'build/aspect-process-parent' if parent_render else OUT
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
    if break_owner:
        import build_break_owner as breaker
        breaker.main(banked=True)
        objects += [str(breaker.OUT/(name+'.obj')) for name in ('install','restore','ignore','break_binding','break_owner_far')]
    state=ROOT/'src/process/native_process_state.asm';obj=output/'native_process_state.obj'
    subprocess.run(['nasm','-fobj','-DNATIVE_PROCESS_SHARED_PATH','-DASPECT_EXTERNAL_UNWIND',str(state),'-o',str(obj)],check=True);objects.append(str(obj))
    c_sources=[ROOT/p for p in ('src/process/native_process.c','src/process/native_display.c',
        'src/process/native_program.c','src/aspect/process_serial.c','src/process/process_handles.c','src/aspect/external_runtime.c')]
    if break_owner:
        # Keep near CRT/platform calls in _TEXT through explicit far adapters.
        flags=['-DASPECT_EXTERNAL_PROCESS','-DASPECT_EXTERNAL_UNWIND','-DNATIVE_PROGRAM_BREAK_OWNER',
               '-DNATIVE_BREAK_FAR','-DNATIVE_PROGRAM_FAR']
        if driver:flags+=['-DASPECT_EXTERNAL_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC']
        controller=output/'native_program_far.obj'
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',
            *flags,'-nt=PROGRAMCODE','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'src/process'),
            '-fo='+str(controller),str(ROOT/'src/process/native_program.c')],cwd=output,check=True)
        objects.append(str(controller))
        c_sources.remove(ROOT/'src/process/native_program.c');c_sources.append(ROOT/'src/process/program_bank.c')
        objects.remove(str(program.OUT/'program_ui.obj'))
        ui_binding=output/'program_ui_bank.obj'
        subprocess.run(['nasm','-fobj','-DNATIVE_PROGRAM_FAR',str(ROOT/'src/process/program_ui.asm'),'-o',str(ui_binding)],check=True)
        objects.append(str(ui_binding))
        exit_binding=output/'exit_owner.obj'
        subprocess.run(['nasm','-fobj',str(ROOT/'src/process/exit_owner.asm'),'-o',str(exit_binding)],check=True)
        objects.append(str(exit_binding))
        c_sources += [ROOT/'src/process/exit_owner.c',ROOT/'src/aspect/exit_runtime.c']
    sources=[ROOT/name for name in manifest['sources']]
    if break_owner:
        sources += [ROOT/name for name in json.loads((breaker.OUT/'manifest.json').read_text())['sources']]
        sources += [ROOT/'src/process/program_bank.h']
        sources += [ROOT/'src/process/exit_owner.h',ROOT/'src/process/exit_owner.asm']
    sources += c_sources+[ROOT/'src/process/process_handles.h',ROOT/'src/aspect/external_runtime.h',ROOT/'src/aspect/external_unwind.h',Path(__file__)]
    extension=dict(output=output,objects=objects,c_sources=c_sources,sources=sources,parent_render=parent_render,break_owner=break_owner)
    if driver:extension['driver']=driver;extension['sources'].append(driver)
    runner.main(extension)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent-render',action='store_true');parser.add_argument('--fault-diagnostic',action='store_true')
    parser.add_argument('--break-owner',action='store_true')
    args=parser.parse_args()
    if args.fault_diagnostic:main(ROOT/'standalone/aspect_fault_driver.c',parent_render=True,output=ROOT/('build/aspect-fault-break' if args.break_owner else 'build/aspect-fault'),break_owner=args.break_owner)
    else:main(parent_render=args.parent_render,output=ROOT/'build/aspect-process-break' if args.break_owner else None,break_owner=args.break_owner)
