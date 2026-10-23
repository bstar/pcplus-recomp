#!/usr/bin/env python3
"""Build the maintained DOS ASPECT CLI without original or fixture inputs."""
import json
from pathlib import Path
import subprocess
from build_aspect_runtime import ROOT, ASM, sha

OUT = ROOT / 'build/aspect-runner'


def main(extension=None):
    # Only the separately named experimental process builder supplies this.
    # Default production inputs/flags and opcode coverage remain unchanged.
    output=extension['output'] if extension else OUT
    feature_flags=['-DASPECT_EXTERNAL_PROCESS','-DASPECT_EXTERNAL_COMMANDS','-DASPECT_EXTERNAL_UNWIND'] if extension else []
    if extension and extension.get('parent_render'):feature_flags.append('-DASPECT_EXTERNAL_RENDER')
    if extension and extension.get('program_far'):feature_flags+=['-DNATIVE_PROGRAM_FAR']
    if extension and extension.get('notice_bank'):feature_flags+=['-DNATIVE_PROGRAM_NOTICES','-DNOTICE_BANKED']
    if extension and extension.get('notice_sound'):feature_flags+=['-DPROGRAM_NOTICE_SPEAKER','-DNOTICE_SPEAKER','-DSPEAKER_BANKED','-DASPECT_SOUND_POLICY']
    if extension and extension.get('notice_input'):feature_flags+=['-DASPECT_NOTICE_INPUT','-DNOTICE_NATIVE_INPUT','-DMOUSE_NOTICE_INPUT']
    if extension and extension.get('break_owner'):feature_flags+=['-DNATIVE_PROGRAM_BREAK_OWNER','-DNATIVE_BREAK_FAR','-DNATIVE_PROGRAM_FAR']
    main_source=extension.get('driver',ROOT/'src/aspect/runner.c') if extension else ROOT/'src/aspect/runner.c'
    diagnostic_driver=main_source!=ROOT/'src/aspect/runner.c' and not (extension and extension.get('focused_notice'))
    if extension and extension.get('focused_notice'):feature_flags+=['-DPROGRAM_NOTICE_DIAGNOSTIC']
    if extension and diagnostic_driver:feature_flags+=['-DASPECT_EXTERNAL_DIAGNOSTIC','-DNATIVE_DISPLAY_DIAGNOSTIC']
    if main_source.name=='aspect_process_diagnostic.c':feature_flags.append('-DASPECT_PROCESS_OBSERVER_FAR')
    output.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    objects = []
    sources = [Path(__file__).resolve(), ROOT / 'standalone/build_aspect_runtime.py',
               *[ROOT / 'src/aspect' / name for name in ['runner.c', 'runtime.c', 'runtime.h', 'file_io.c', 'file_io.h', 'script_path.c', 'script_path.h',
                   'serial_runtime.c','serial_runtime.h','serial_wait.c','receive_runtime.c','receive_runtime.h','when_runtime.c','when_runtime.h','set_runtime.c','set_runtime.h','find_runtime.c','find_runtime.h','environment_runtime.c','environment_runtime.h','script_file_runtime.c','script_file_runtime.h','file_info_runtime.c','file_info_runtime.h','file_times_runtime.c','file_times_runtime.h','enumeration_runtime.c','enumeration_runtime.h','txpace.c','txpace.h','directory_runtime.c','directory_runtime.h','serial.c','serial.h','serial_handoff.h','resident_render.c','resident_render.h','source_compile.c','source_compile.h']],
               ROOT/'reconstruction/translation/receive.asm', ROOT / 'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',
               ROOT/'src/config/resource_path.c',ROOT/'src/config/resource_path.h',
               ROOT/'src/keyboard/api.h',
               ROOT/'reconstruction/directory_accounting/patch.asm']
    compiled_sources=[p for p in sources if p.suffix=='.c']
    serial_asm=[('uart','reconstruction/uart/core.asm','UART_OMF'),('uart_api','src/uart/api.asm',None),
                ('txpace','src/aspect/txpace.asm',None),
                ('serial_backend','src/aspect/serial_backend.asm',None),
                ('resident_client','src/aspect/resident_render_client.asm',None),
                ('abort_confirm','src/aspect/abort_confirm.asm',None),
                ('abort_yesno','reconstruction/script_abort/confirm.asm','ABORT_CONFIRM_OMF')]
    if extension:
        sources += extension['sources']
        compiled_sources=[p for p in compiled_sources if p!=ROOT/'src/aspect/runner.c']+[main_source,*extension['c_sources']]
        serial_asm += [('process_serial','src/aspect/process_serial.asm',None),
                       ('external_unwind','src/aspect/external_unwind.asm',None),
                       ('external_commands','src/aspect/external_commands.asm',None)]
    for name, relative, define in ASM+serial_asm:
        source, obj = ROOT / relative, output / (name + '.obj')
        sources.append(source)
        abort_flags=[]
        if name=='abort_yesno':
            abort_flags=['-DABORT_CONFIRM_YESNO_ONLY']
            abort_flags += ['-D'+key+'='+value for key,value in {
                'abort_choice_no':'_runtime_abort_no','abort_choice_yes':'_runtime_abort_yes',
                'abort_choice_cursor_mode':'_runtime_abort_cursor_mode','abort_choice_last_key':'_runtime_abort_last_key',
                'abort_cursor_push':'_runtime_abort_ui_begin','abort_cursor_pop':'_runtime_abort_ui_end',
                'abort_cursor_enable':'_runtime_abort_ui_invalid','abort_cursor_disable':'_runtime_abort_ui_invalid',
                'abort_choice_key_read':'_runtime_abort_read_key','abort_choice_bell':'_runtime_abort_bell'}.items()]
        subprocess.run(['nasm', '-f', 'obj', include] + feature_flags + abort_flags + (['-D' + define] if define else []) +
                       (['-DASPECT_RUNTIME_SERIAL'] if name in ('bridge','dispatch') else []) +
                       (['-DASPECT_SOURCE_OUTPUT'] if name=='dispatch' else []) +
                       [str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    if extension:objects += extension['objects']
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192','-dASPECT_RUNTIME_SERIAL',
                    *(['-ob','-os'] if extension else []),
                    *feature_flags, *(['-DNATIVE_PROCESS_DIAGNOSTIC'] if extension else []),
                    '-i=' + str(ROOT / 'src/aspect'), '-i='+str(ROOT/'src/process'), '-fm=ASPECT.map', '-fe=ASPECT.EXE',
                    str(main_source), str(ROOT / 'src/aspect/runtime.c'),str(ROOT/'src/aspect/environment_runtime.c'),str(ROOT/'src/aspect/script_file_runtime.c'),str(ROOT/'src/aspect/file_info_runtime.c'),str(ROOT/'src/aspect/file_times_runtime.c'),str(ROOT/'src/aspect/enumeration_runtime.c'),
                    str(ROOT / 'src/aspect/file_io.c'),str(ROOT/'src/aspect/source_compile.c'),str(ROOT/'src/aspect/script_path.c'),str(ROOT/'src/aspect/serial_runtime.c'),str(ROOT/'src/aspect/serial_wait.c'),str(ROOT/'src/aspect/receive_runtime.c'),
                    str(ROOT/'src/aspect/serial.c'),str(ROOT/'src/aspect/directory_runtime.c'),str(ROOT/'src/aspect/resident_render.c'),str(ROOT/'src/aspect/when_runtime.c'),str(ROOT/'src/aspect/set_runtime.c'),str(ROOT/'src/aspect/find_runtime.c'),str(ROOT/'src/aspect/txpace.c'),str(ROOT/'src/config/resource_path.c'),
                    *([str(p) for p in extension['c_sources']] if extension else []),*objects], cwd=output, check=True)
    result = dict(binary_sha256=sha(output / 'ASPECT.EXE'), original_inputs=[],
                  source_extensions={'D7/01':'TRANSMITRAW hexadecimal bytes; requires maintained runtime, not legacy ASX portable'},
                  objects={p.name:sha(p) for p in [*[Path(p) for p in objects],
                      *[output/(p.stem+'.o') for p in compiled_sources]]},
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  platform='8086 DOS, small model, near DS=SS, cdecl, 8192-byte stack',
                  diagnostic_build=False,
                  scope='DOS CLI for trusted ASX and maintained ASP compilation; partial105-slot runtime with native WHEN/CWHEN, thirteen SET/FETCH families and owned six-slot streams. Capability12 uses the real parent parser, selected key profile, cooperative help and native yes/no confirmation with child-owned receive. Raw ASIO retains immediate cancellation and queued raw delay semantics. Full language, command actions, other waits/flows, physical timing and arbitrary-bytecode safety remain unfinished.')
    if extension:
        result.update(experimental_external_commands=True,production_dispatch_changed=False,
            experimental_break_owner=bool(extension.get('break_owner')),
            experimental_fault_unwind=True,compiler_size_optimized=True,
            experimental_parent_render=bool(extension.get('parent_render')),
            diagnostic_build=diagnostic_driver,
            main_source=str(main_source.relative_to(ROOT)),
            scope='Experimental108-slot raw/local ASPECT with composed PROGRAM, private DOS handles and real script/ASX ownership checks. Attached parent rendering rejects before execution; full application publication remains open.')
        if extension.get('parent_render'):result['scope']='Experimental108-slot ASPECT with capability13 attached parent PROGRAM lease, cooperative help/native yes-no confirmation, private streams and the PROGRAMCODE far controller through explicit near-platform adapters. Break/exit policy is selected separately. The normal105-slot application, complete command ownership and physical acceptance remain separate gates.'
    (output / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('ASPECT.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
