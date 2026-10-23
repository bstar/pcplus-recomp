#!/usr/bin/env python3
"""Build experimental full-VM external commands; do not replace shipped ASPECT."""
import json,subprocess
from pathlib import Path
import build_native_program as program
import build_aspect_runner as runner
ROOT=program.ROOT;OUT=ROOT/'build/aspect-process';sha=program.sha


def main(driver=None,parent_render=False,output=None,break_owner=False,notice_bank=False,notice_sound=False,notice_input=False,notice_help=False,help_resource=False,serial_bank=False):
    if notice_help:assert notice_input
    if help_resource:assert notice_help
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
    # All external-command variants need the existing PROGRAMCODE bank as the
    # ordinary VM grows. This changes placement, not Break/exit policy.
    # Keep near CRT/platform calls in _TEXT through explicit far adapters.
    flags=['-DASPECT_EXTERNAL_PROCESS','-DASPECT_EXTERNAL_UNWIND','-DNATIVE_PROGRAM_FAR']
    if notice_bank:flags+=['-DNATIVE_PROGRAM_NOTICES','-DNOTICE_BANKED']
    if notice_sound:flags+=['-DPROGRAM_NOTICE_SPEAKER','-DNOTICE_SPEAKER','-DSPEAKER_BANKED','-DASPECT_SOUND_POLICY']
    if notice_input:flags+=['-DASPECT_NOTICE_INPUT','-DNOTICE_NATIVE_INPUT','-DMOUSE_NOTICE_INPUT']
    if notice_help:flags+=['-DASPECT_NOTICE_HELP']
    if help_resource:flags+=['-DASPECT_HELP_RESOURCE']
    if break_owner:flags+=['-DNATIVE_PROGRAM_BREAK_OWNER','-DNATIVE_BREAK_FAR']
    focused_notice=bool(driver and driver.name=='aspect_notice_driver.c')
    if notice_help and focused_notice:flags+=['-DHELP_VIEW_DIAGNOSTIC']
    if driver and not focused_notice:flags+=['-DASPECT_EXTERNAL_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC']
    if focused_notice:flags+=['-DPROGRAM_NOTICE_DIAGNOSTIC']
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
    if break_owner:
        exit_binding=output/'exit_owner.obj'
        subprocess.run(['nasm','-fobj',str(ROOT/'src/process/exit_owner.asm'),'-o',str(exit_binding)],check=True)
        objects.append(str(exit_binding))
        c_sources += [ROOT/'src/process/exit_owner.c',ROOT/'src/aspect/exit_runtime.c']
    sources=[ROOT/name for name in manifest['sources']]
    sources += [ROOT/'src/process/program_bank.h']
    if break_owner:
        sources += [ROOT/name for name in json.loads((breaker.OUT/'manifest.json').read_text())['sources']]
        sources += [ROOT/'src/process/exit_owner.h',ROOT/'src/process/exit_owner.asm']
    sources += c_sources+[ROOT/'src/process/process_handles.h',ROOT/'src/aspect/external_runtime.h',ROOT/'src/aspect/external_unwind.h',Path(__file__)]
    if notice_bank:
        import build_notice_bank as notice
        notice.main()
        if notice_sound:
            import build_speaker_notice as sound
            sound.main()
        nm=json.loads((ROOT/'build/notice-bank/manifest.json').read_text())
        objects += [str(ROOT/path) for path in nm['production_objects']]
        sources += [ROOT/path for path in nm['sources']]
        if notice_sound:
            sm=json.loads((ROOT/'build/speaker-notice/manifest.json').read_text())
            sources += [ROOT/path for path in sm['sources']]
            sources += [ROOT/path for path in json.loads((ROOT/'build/notice-bank-uart/manifest.json').read_text())['sources']]
            objects += [str(ROOT/'build/speaker'/name) for name in ('speaker.obj','backend.obj')]
        if notice_input:
            from build_notice_input_bank import build as build_input
            input_objects,input_sources=build_input(output,help_view=notice_help,help_diagnostic=notice_help and focused_notice,help_resource=help_resource)
            objects += input_objects;sources += [ROOT/x for x in input_sources]
            runtime=output/'notice-input-runtime.obj'
            subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',*flags,'-nt=NOTICECODE','-fo='+str(runtime),str(ROOT/'src/ui/notice.c')],cwd=output,check=True)
        # Reuse identical far CRT bridges already provided by PROGRAMCODE's
        # platform. Only OMF import names change; code/data/fixups stay exact.
        from omf_imports import records,externals,rename_imports
        aliases={'_notice_bank_int86':'_program_bank_int86','_notice_bank_memset':'_program_bank_memset'}
        for name in ['owner-normal','runtime']:
            original=ROOT/'build/notice-bank'/(name+'.obj')
            source_object=ROOT/'build/notice-bank/owner.obj' if focused_notice and name=='owner-normal' else ROOT/'build/speaker-notice/runtime.obj' if notice_sound and name=='runtime' else original
            if notice_input and name=='runtime':source_object=runtime
            blob=source_object.read_bytes()
            imports={n.decode() for kind,payload,_ in records(blob) if kind==0x8c for n,_ in externals(payload)}
            rewritten,_=rename_imports(blob,{a:b for a,b in aliases.items() if a in imports})
            obj=output/('notice-shared-'+name+'.obj');obj.write_bytes(rewritten)
            objects[objects.index(str(original))]=str(obj)
        original=ROOT/'build/notice-bank/notice_bank.o';obj=output/'notice_platform.obj'
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-DNOTICE_PROGRAM_ADAPTERS','-fo='+str(obj),str(ROOT/'src/ui/notice_bank.c')],cwd=output,check=True)
        objects[objects.index(str(original))]=str(obj);sources.append(ROOT/'standalone/omf_imports.py')
        notice_source=ROOT/'src/process/program_notice.c';obj=output/'program_notice.obj'
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we',*flags,'-nt=NOTICECODE','-fo='+str(obj),str(notice_source)],cwd=output,check=True)
        objects.append(str(obj));sources += [notice_source,ROOT/'src/process/program_notice.h']
        if focused_notice:
            original=native.OUT/'exec.obj';objects.remove(str(original))
            obj=output/'notice_exec.obj';source=ROOT/'reconstruction/program_exec/exec.asm'
            subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/','-DPROGRAM_EXEC_OMF','-DPROGRAM_NOTICE_DIAGNOSTIC',str(source),'-o',str(obj)],check=True);objects.append(str(obj))
            probe=ROOT/'standalone/notice_fault_probe.c';obj=output/'notice_fault_probe.obj'
            subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we',*flags,'-nt=NOTICECODE','-i='+str(ROOT/'src/aspect'),'-fo='+str(obj),str(probe)],cwd=output,check=True)
            objects.append(str(obj));asm=ROOT/'standalone/notice_fault_native.asm';obj=output/'notice_fault_native.obj'
            subprocess.run(['nasm','-fobj',*(['-DPROGRAM_NOTICE_SPEAKER'] if notice_sound else []),str(asm),'-o',str(obj)],check=True);objects.append(str(obj))
            platform=ROOT/'standalone/notice_fault_platform.c';c_sources.append(platform)
            sources += [probe,asm,platform,ROOT/'standalone/notice_fault.h']
    if help_resource:
        from build_help_resource import generate
        resource=generate(output/'LOCHELP.HLP');sources += [ROOT/n for n in resource['sources']]
        (output/'help-resource.json').write_text(json.dumps(resource,indent=2)+'\n')
    extension=dict(output=output,objects=objects,c_sources=c_sources,sources=sources,parent_render=parent_render,break_owner=break_owner,program_far=True,notice_bank=notice_bank,focused_notice=focused_notice,notice_sound=notice_sound,notice_input=notice_input,notice_help=notice_help,help_resource=help_resource,serial_bank=serial_bank)
    if driver:extension['driver']=driver;extension['sources'].append(driver)
    runner.main(extension)
    if notice_bank:
        path=output/'manifest.json';result=json.loads(path.read_text())
        result['experimental_notice_bank_linked']=True
        result['experimental_notice_error_binding']=True
        result['experimental_notice_sound_binding']=notice_sound
        result['experimental_notice_input_binding']=notice_input
        result['experimental_notice_help_binding']=notice_help
        result['experimental_help_resource']=help_resource
        result['notice_PROGRAM_binding_accepted']=False
        path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parent-render',action='store_true');parser.add_argument('--fault-diagnostic',action='store_true')
    parser.add_argument('--break-owner',action='store_true')
    parser.add_argument('--notice-input',action='store_true')
    parser.add_argument('--notice-help',action='store_true')
    parser.add_argument('--help-resource',action='store_true')
    parser.add_argument('--serial-bank',action='store_true')
    parser.add_argument('--notice-sound',action='store_true',help='Experimental parent sound policy and serviced speaker binding')
    parser.add_argument('--notice-bank',action='store_true',help='Bind banked PROGRAM error notices in a separate experimental parent')
    args=parser.parse_args()
    if args.notice_sound:assert args.notice_bank
    if args.notice_input:assert args.notice_sound
    if args.notice_help:assert args.notice_input
    if args.help_resource:assert args.notice_help
    if args.serial_bank:
        assert args.help_resource and not args.fault_diagnostic and not args.break_owner
        main(parent_render=True,output=ROOT/'build/aspect-serial-bank-parent',notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,help_resource=True,serial_bank=True)
    elif args.notice_bank:
        assert not args.break_owner
        main(ROOT/'standalone/aspect_notice_driver.c' if args.fault_diagnostic else None,parent_render=True,output=ROOT/(('build/aspect-help-resource-fault' if args.fault_diagnostic else 'build/aspect-help-resource-parent') if args.help_resource else ('build/aspect-notice-help-fault' if args.fault_diagnostic else 'build/aspect-notice-help-parent') if args.notice_help else ('build/aspect-notice-input-fault' if args.fault_diagnostic else 'build/aspect-notice-input-parent') if args.notice_input else ('build/aspect-notice-sound-fault' if args.fault_diagnostic else 'build/aspect-notice-sound-parent') if args.notice_sound else ('build/aspect-notice-fault' if args.fault_diagnostic else 'build/aspect-notice-parent')),notice_bank=True,notice_sound=args.notice_sound,notice_input=args.notice_input,notice_help=args.notice_help,help_resource=args.help_resource)
    elif args.fault_diagnostic:main(ROOT/'standalone/aspect_fault_driver.c',parent_render=True,output=ROOT/('build/aspect-fault-break' if args.break_owner else 'build/aspect-fault'),break_owner=args.break_owner)
    else:main(parent_render=args.parent_render,output=ROOT/'build/aspect-process-break' if args.break_owner else None,break_owner=args.break_owner)
