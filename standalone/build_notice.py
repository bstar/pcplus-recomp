#!/usr/bin/env python3
"""Compose the exact timed notice core with owned windows and foreground gates."""
import hashlib,json,subprocess
from pathlib import Path
import build_notice_window as window
ROOT=window.ROOT;OUT=ROOT/'build/notice'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    window.main();OUT.mkdir(parents=True,exist_ok=True);wm=json.loads((window.OUT/'manifest.json').read_text());include='-I'+str(ROOT/'reconstruction/uart')+'/'
    objects=[str(window.OUT/(u['name']+'.obj')) for u in wm['units']]+[str(window.OUT/'binding.obj')]
    sources=dict(wm['sources']);sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    for name,path,flags in [('core','reconstruction/program_notice/core.asm',['PROGRAM_NOTICE_OMF']),('strlen','reconstruction/program_exec/strlen.asm',['PROGRAM_EXEC_OMF']),('clock','reconstruction/transfer_uart/clock.asm',['TRANSFER_UART_OMF']),('text','reconstruction/program_ui/text.asm',['PROGRAM_DISPLAY_OMF']),('binding','src/ui/notice_native.asm',['_notice_ticks_native=_notice_actual_ticks']),('probe','standalone/notice_clock_probe.asm',[])]:
        source=ROOT/path;obj=OUT/(name+'.obj');subprocess.run(['nasm','-fobj',include,*['-D'+flag for flag in flags],str(source),'-o',str(obj)],check=True);objects.append(str(obj));sources[path]=sha(source)
    checkpoint=ROOT/'src/ui/notice_checkpoint.asm';checkpoint_object=OUT/'checkpoint.obj'
    subprocess.run(['nasm','-fobj',str(checkpoint),'-o',str(checkpoint_object)],check=True);objects.append(str(checkpoint_object));sources[str(checkpoint.relative_to(ROOT))]=sha(checkpoint)
    owner=ROOT/'src/ui/notice_window.c';runtime=ROOT/'src/ui/notice.c';host=ROOT/'standalone/notice_diagnostic.c'
    for path in [runtime,host,ROOT/'src/ui/notice.h',ROOT/'reconstruction/program_notice/provenance.json']:sources[str(path.relative_to(ROOT))]=sha(path)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dNOTICE_WINDOW_DIAGNOSTIC','-i='+str(ROOT/'src/ui'),'-fm=NOTICE.map','-fe=NOTICE.EXE',str(owner),str(runtime),str(host),*objects],cwd=OUT,check=True)
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-i='+str(ROOT/'src/ui'),'-fo='+str(OUT/'notice-normal.obj'),str(runtime)],cwd=OUT,check=True)
    m=dict(original_inputs=[],sources=sources,binary_sha256=sha(OUT/'NOTICE.EXE'),normal_runtime_compiled=True,window_products=wm['products'],scope='Composed native timed controller/window/video, source-owned allocation, foreground callback, real BIOS/DOS keys/clocks and typed nonlocal cleanup. Component only; application binding and original sound/macro/shared-parent policies remain open.')
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('Built NOTICE.EXE')
if __name__=='__main__':main()
