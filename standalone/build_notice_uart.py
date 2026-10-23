#!/usr/bin/env python3
"""Compose notice foreground service with the actual UART ISR/flow owner."""
import hashlib,json,subprocess
from pathlib import Path
import build_notice
ROOT=build_notice.ROOT;OUT=ROOT/'build/notice-uart'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    build_notice.main();OUT.mkdir(parents=True,exist_ok=True)
    m=json.loads((build_notice.OUT/'manifest.json').read_text());wm=json.loads((ROOT/'build/notice-window/manifest.json').read_text());sources=dict(m['sources']);sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    objects=[str(ROOT/'build/notice-window'/(u['name']+'.obj')) for u in wm['units']]+[str(ROOT/'build/notice-window/binding.obj')]+[str(build_notice.OUT/(name+'.obj')) for name in ['core','strlen','text','checkpoint']]
    include='-I'+str(ROOT/'reconstruction/uart')+'/'
    for name,path,flags in [('uart','reconstruction/uart/core.asm',['UART_OMF']),('api','src/uart/api.asm',[]),('serial_backend','src/aspect/serial_backend.asm',[])]:
        source=ROOT/path;obj=OUT/(name+'.obj');subprocess.run(['nasm','-fobj',include,*['-D'+flag for flag in flags],str(source),'-o',str(obj)],check=True);objects.append(str(obj));sources[path]=sha(source)
    for name,path,define in [('clock','reconstruction/transfer_uart/clock.asm','TRANSFER_UART_OMF'),('notice_binding','src/ui/notice_native.asm',None)]:
        obj=OUT/(name+'.obj');subprocess.run(['nasm','-fobj',include,'-Dpcplus_seconds=notice_seconds_recovered',*(['-D'+define] if define else []),str(ROOT/path),'-o',str(obj)],check=True);objects.append(str(obj))
    c_sources=[ROOT/path for path in ['src/ui/notice_window.c','src/ui/notice.c','src/aspect/serial.c','standalone/notice_uart_diagnostic.c']]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/ui'),'-i='+str(ROOT/'src/aspect'),'-fm=NUART.map','-fe=NUART.EXE',*[str(path) for path in c_sources],*objects],cwd=OUT,check=True)
    for path in [*c_sources,ROOT/'src/aspect/serial.h',ROOT/'src/aspect/serial_handoff.h',ROOT/'src/aspect/resident_render.h',ROOT/'reconstruction/uart/layout.inc',ROOT/'reconstruction/directory_accounting/patch.asm']:sources[str(path.relative_to(ROOT))]=sha(path)
    result=dict(original_inputs=[],sources=sources,binary_sha256=sha(OUT/'NUART.EXE'),notice_binary_sha256=m['binary_sha256'],clock_symbol='notice_seconds_recovered',scope='Actual UART/ISR/flow owner polled during the native timed notice; raw input retained until the window closes. Diagnostic driver only; no PROGRAM, BBS or physical UART acceptance.')
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built NUART.EXE')
if __name__=='__main__':main()
