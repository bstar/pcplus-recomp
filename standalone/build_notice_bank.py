#!/usr/bin/env python3
"""Build the complete notice/window runtime in a separate DOS code bank."""
import hashlib,json,re,subprocess
from pathlib import Path
import build_notice_window as window
ROOT=window.ROOT
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    window.main()
    wm=json.loads((window.OUT/'manifest.json').read_text())
    sources=dict(wm['sources'])
    for name in ['standalone/build_notice_bank.py','src/ui/notice_bank.c','src/ui/notice_bank.h','src/ui/notice.c','src/ui/notice.h','src/ui/notice_unwind.h','src/ui/notice_checkpoint.asm','standalone/notice_diagnostic.c','standalone/notice_clock_probe.asm','standalone/notice_bank_probe.asm']:
        sources[name]=sha(ROOT/name)
    units=[(u['name'],u['file'],[u['define']]) for u in wm['units']]
    units += [('window-binding','src/ui/notice_window_native.asm',[]),('core','reconstruction/program_notice/core.asm',['PROGRAM_NOTICE_OMF']),('strlen','reconstruction/program_exec/strlen.asm',['PROGRAM_EXEC_OMF']),('clock','reconstruction/transfer_uart/clock.asm',['TRANSFER_UART_OMF']),('text','reconstruction/program_ui/text.asm',['PROGRAM_DISPLAY_OMF']),('binding','src/ui/notice_native.asm',[]),('checkpoint','src/ui/notice_checkpoint.asm',[])]
    # Isolate the reused display/CRT helper exports from the application's other
    # native components. Every defining and consuming object gets this mapping.
    names=set()
    for _,path,_ in units:
        names.update(re.findall(r'\b(?:display_\w+|text_video_segment|text_cga_status_port|ui_read_byte|program_strlen|pcplus_seconds|transfer_dos_time|transfer_dos_clock_sample)\b',(ROOT/path).read_text()))
        sources[path]=sha(ROOT/path)
    aliases={name:'notice_'+name for name in sorted(names)}
    for uart in [False,True]:
        out=ROOT/('build/notice-bank-uart' if uart else 'build/notice-bank');out.mkdir(parents=True,exist_ok=True)
        objects=[];current=dict(sources)
        def assembly(name,path,defines=(),bank=True,link=True):
            obj=out/(name+'.obj')
            flags=['-D'+d for d in defines]
            if bank:flags += ['-D_TEXT=NOTICECODE','-DNOTICE_CHECKPOINT_SEGMENT=NOTICECODE',*['-D'+a+'='+b for a,b in aliases.items()]]
            subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,str(ROOT/path),'-o',str(obj)],check=True)
            if link:objects.append(str(obj))
            current[path]=sha(ROOT/path)
            return str(obj)
        for name,path,defines in units:
            if name=='binding' and not uart:defines=[*defines,'_notice_ticks_native=_notice_actual_ticks']
            assembly(name,path,defines)
        production_objects=[p for p in objects if Path(p).name!='binding.obj']
        production_objects.append(assembly('binding-production','src/ui/notice_native.asm',link=False))
        if not uart:
            assembly('clock-probe','standalone/notice_clock_probe.asm',['NOTICE_BANKED'])
            assembly('bank-probe','standalone/notice_bank_probe.asm')
        else:
            for name,path,defines in [('uart','reconstruction/uart/core.asm',['UART_OMF']),('api','src/uart/api.asm',[]),('serial-backend','src/aspect/serial_backend.asm',[])]:assembly(name,path,defines,bank=False)
            for path in ['src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/resident_render.h','reconstruction/uart/layout.inc','reconstruction/directory_accounting/patch.asm']:current[path]=sha(ROOT/path)
        flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dNOTICE_BANKED','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/aspect')]
        for name,path in [('owner','src/ui/notice_window.c'),('runtime','src/ui/notice.c')]:
            obj=out/(name+'.obj')
            subprocess.run(['wcc',*flags,*(['-dNOTICE_WINDOW_DIAGNOSTIC'] if not uart else []),'-nt=NOTICECODE','-fo='+str(obj),str(ROOT/path)],cwd=out,check=True)
            objects.append(str(obj));current[path]=sha(ROOT/path)
        # Also compile the production owner without allocation-failure hooks.
        subprocess.run(['wcc',*flags,'-nt=NOTICECODE','-fo='+str(out/'owner-normal.obj'),str(ROOT/'src/ui/notice_window.c')],cwd=out,check=True)
        c_paths=['src/ui/notice_bank.c',*(['src/aspect/serial.c','standalone/notice_uart_diagnostic.c'] if uart else ['standalone/notice_diagnostic.c'])]
        binary='NUART' if uart else 'NOTICE'
        subprocess.run(['wcl',*flags,*(['-dNOTICE_WINDOW_DIAGNOSTIC'] if not uart else []),'-k8192','-fd='+binary+'.lnk','-fm='+binary+'.map','-fe='+binary+'.EXE',*[str(ROOT/path) for path in c_paths],*objects],cwd=out,check=True)
        with (out/(binary+'.lnk')).open('a') as stream:stream.write('\noption packcode=0\n')
        subprocess.run(['wlink','@'+str(out/(binary+'.lnk'))],cwd=out,check=True)
        for path in c_paths:current[path]=sha(ROOT/path)
        manifest=dict(original_inputs=[],sources=current,binary_sha256=sha(out/(binary+'.EXE')),banked=True,owner_normal_compiled=True,aliases=aliases,window_products=wm['products'],scope=__doc__+' Explicit far CRT and near-callback adapters; native helper exports isolated. Component only; PROGRAM/shared-parent/fault and physical integration remain open.')
        manifest['production_objects']=[str(Path(p).relative_to(ROOT)) for p in [*production_objects,str(out/'owner-normal.obj'),str(out/'runtime.obj'),str(out/'notice_bank.o')]]
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('Built '+str(out.relative_to(ROOT))+'/'+binary+'.EXE')
if __name__=='__main__':main()
