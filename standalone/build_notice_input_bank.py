"""Link child-owned mouse/keyboard and notice input entirely outside near CODE."""
import json,re,subprocess
from pathlib import Path
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1]

def build(output,help_view=False,help_diagnostic=False,help_resource=False):
    assert not help_diagnostic or help_view
    assert not help_resource or help_view
    objects=[];sources=[]
    names=['read','peek','poll','normalize_bios','bios_read','bios_peek','queue_read','read_extended','normalize_extended',
        'queue_count','queue_index','queue_active','queue_peek','queue_values','debug_gate','debug_callback']
    aliases=['-Dkeyboard_'+n+'=notice_input_keyboard_'+n for n in names]
    aliases+=['-Dkeyboard_bios_mode=_runtime_keyboard_mode']
    flags=['-D_TEXT=NOTICEINPUT_CODE','-DCODE=FARCODE',*aliases]
    native=json.loads((ROOT/'reconstruction/program_mouse/provenance.json').read_text())
    units=[(x['file'],['PROGRAM_MOUSE_OMF']) for x in native['units']]
    units += [('reconstruction/program_mouse/defaults.asm',['PROGRAM_MOUSE_OMF']),
        ('reconstruction/keyboard/core.asm',['KEYBOARD_OMF']),('src/mouse/state.asm',['MOUSE_EXTERNAL_BIOS']),
        ('src/mouse/platform.asm',[]),('src/mouse/dos_memory.asm',[]),('src/ui/notice_input_bios.asm',[]),('src/process/exit_owner.asm',[])]
    for i,(path,defines) in enumerate(units):
        obj=output/f'notice-mouse-{i}.obj'
        subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,*['-D'+d for d in defines],str(ROOT/path),'-o',str(obj)],check=True)
        objects.append(str(obj));sources.append(path)
    if help_view:
        path='src/help/view_cursor.asm';obj=output/'help-cursor.obj'
        subprocess.run(['nasm','-fobj',str(ROOT/path),'-o',str(obj)],check=True)
        objects.append(str(obj));sources.append(path)
    if help_resource:
        path='src/help/resource_io.asm';obj=output/'help-resource-io.obj'
        subprocess.run(['nasm','-fobj',str(ROOT/path),'-o',str(obj)],check=True)
        objects.append(str(obj));sources.append(path)
    c_units=['src/mouse/owner.c','src/ui/notice_input.c','src/process/exit_owner.c','src/ui/notice_input_exit.c']
    if help_view:c_units+=['src/help/view.c','src/help/notice_content.c']
    if help_resource:c_units+=['src/help/format.c','src/help/document.c','src/help/resource.c']
    for path in c_units:
        obj=output/('input-'+Path(path).stem+'.obj')
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-dNOTICE_BANKED','-dMOUSE_NOTICE_INPUT','-dMOUSE_DOS_PLATFORM','-dNOTICE_INPUT_BIOS_FALLBACK','-dNOTICE_INPUT_EXIT_GUARD','-dPROGRAM_EXIT_NO_BREAK','-dASPECT_EXTERNAL_PROCESS',*(['-dASPECT_NOTICE_HELP'] if help_view else []),*(['-dHELP_VIEW_DIAGNOSTIC'] if help_diagnostic else []),*(['-dASPECT_HELP_RESOURCE'] if help_resource else []),'-nt=NOTICEINPUT_CODE','-nc=FARCODE','-fo='+str(obj),str(ROOT/path)],cwd=output,check=True)
        imports={n.decode() for kind,payload,_ in records(obj.read_bytes()) if kind==0x8c for n,_ in externals(payload)}
        assert all(n.startswith(('_mouse_','_notice_','_program_exit_','_native_','_runtime_external_')) or (help_view and n.startswith('_help_')) or n in ('_small_code_','__STACKTOP','__psp','_process_handles_active','_aspect_process_serial_detached','_aspect_serial_active') for n in imports),imports
        objects.append(str(obj));sources.append(path)
    sources += ['standalone/build_notice_input_bank.py','src/mouse/owner.h','src/ui/notice_input.h','src/ui/notice_input_exit.h','src/process/exit_owner.h','src/process/break_owner.h','reconstruction/program_mouse/provenance.json',
        'reconstruction/program_mouse/defaults.json','reconstruction/keyboard/provenance.json','standalone/omf_imports.py']
    if help_view:sources+=['src/help/view.h','src/help/notice_content.h','src/ui/notice_help.h']
    if help_resource:sources+=['src/help/format.h','src/help/document.h','src/help/resource.h']
    return objects,sources
