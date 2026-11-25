#!/usr/bin/env python3
"""Actual8086 DOS hot ASM/C equality, overlay-no-fetch and raw UART handback.

Uses production serial C, split bank gates, UART core/backend and a diagnostic
counting loader-read adapter. A dummy sibling evicts ASIO; it is not native GET.
Full application GET/source/compiler/renderer acceptance is a separate test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import threading

import test_aspect_serial_translation_dos as original

ROOT=original.ROOT


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
    public=re.findall(r'^SERIAL_ENTRY (_\w+),(\d+)$',(ROOT/'src/aspect/serial_bank.inc').read_text(),re.M)
    callbacks=re.findall(r'^SERIAL_CALLBACK (_\w+),(_\w+),(\d+)$',(ROOT/'src/aspect/serial_bank.inc').read_text(),re.M)
    aliases={name[1:]:name[1:]+'_impl' for name,_ in public}
    aliases.update({target[1:]:name[1:] for name,target,_ in callbacks})
    hot=('directory_entry','directory_record','translate','translation_policy')
    declarations='\n'.join('extern unsigned __far __cdecl reference_'+name+'('+('unsigned' if name=='translate' else 'void')+');' for name in hot)
    declarations+='''
extern unsigned aspect_serial_input_translation_mode,aspect_serial_directory_entry_data;
extern unsigned __cdecl probe_reads(void);
extern void __cdecl probe_reset(void);
extern unsigned __cdecl probe_preserved(void);
extern unsigned __far __cdecl evict_asio(void);
/* These renderer targets are unused in this UART-only profile. */
unsigned aspect_render_active(void){return 0;}
unsigned aspect_render_prepare(unsigned a,unsigned b,unsigned c){return a|b|c|10;}
unsigned aspect_render_attach(void){return 10;}
'''
    assertions='''
 {
  unsigned saved=aspect_serial_input_translation_mode,test_mode,j;
  static unsigned modes[5]={0,1,2,0xff00,0xffff};
  static unsigned entries[5]={0,1,200,0xff00,0xffff};
  for(j=0;j<5;++j){
   aspect_serial_input_translation_mode=modes[j];
   if(aspect_serial_translation_policy()!=reference_translation_policy())return 94;
   for(i=0;;++i){
    if(aspect_serial_translate(i)!=reference_translate(i))return 95;
    if(i==65535U)break;
   }
   aspect_serial_directory_entry_data=entries[j];
   if(aspect_serial_directory_entry()!=reference_directory_entry() ||
      (unsigned)aspect_serial_directory_record()!=reference_directory_record())return 96;
  }
  /* Evict the C reference code, then perform every hot read without any
   * loader read. The returned record pointer continues to address DATA. */
  if(evict_asio()!=0x6d31)return 97;
  if(!probe_reads())return 101;
  probe_reset();
  for(j=0;j<5;++j){
   test_mode=modes[j];aspect_serial_input_translation_mode=test_mode;
   aspect_serial_directory_entry_data=entries[j];
   if(!probe_preserved())return 103;
   if(aspect_serial_translation_policy()!=test_mode ||
      aspect_serial_directory_entry()!=entries[j] ||
      !aspect_serial_directory_record()!=!entries[j])return 98;
   for(i=0;;++i){
    unsigned expected=test_mode==1?((i&255U)^0x55U):(i&255U);
    /* v1/identity modes initialize an identity table. */
    if(test_mode==1 && mode!=1)expected=i&255U;
    if(aspect_serial_translate(i)!=expected)return 99;
    if(i==65535U)break;
   }
  }
  if(probe_reads())return 100;
  if(reference_translation_policy()!=0xffff || !probe_reads())return 102;
  aspect_serial_input_translation_mode=saved;aspect_serial_directory_entry_data=0;
 }
'''
    probe=original.PROBE.replace('#include <stdlib.h>','#include <stdlib.h>\n'+declarations)
    marker=' if(aspect_serial_translation_policy()!=mode)return 82;'
    assert probe.count(marker)==1;probe=probe.replace(marker,marker+assertions)
    (out/'parent.c').write_text(original.PARENT);(out/'probe.c').write_text(probe)
    reference=['BITS 16','CPU 8086','SEGMENT ASIO_CODE public align=16 class=FARCODE use16']
    for name in hot:
        impl='_aspect_serial_'+name+'_impl'
        reference+=['extern '+impl,'global _reference_'+name,'_reference_'+name+':']
        if name=='translate':reference+=['push bp','mov bp,sp','push word [bp+6]','call '+impl,'mov sp,bp','pop bp','retf']
        else:reference+=['call '+impl,'retf']
    reference+=['SEGMENT EVICT_CODE public align=16 class=FARCODE use16','global _evict_asio','_evict_asio: mov ax,0x6d31','retf','times 5623 db 0x5a']
    (out/'reference.asm').write_text('\n'.join(reference)+'\n')
    (out/'read.asm').write_text('''BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _probe_reads,_probe_reset,_probe_preserved
extern _aspect_serial_translate,_aspect_serial_directory_entry
extern _aspect_serial_directory_record,_aspect_serial_translation_policy
%macro CHECK 0
 cmp bx,0xb135
 jne .bad
 cmp bp,0x1256
 jne .bad
 cmp si,0x731f
 jne .bad
 cmp di,0x9d42
 jne .bad
%endmacro
_probe_preserved:
 push bx
 push bp
 push si
 push di
 mov bx,0xb135
 mov bp,0x1256
 mov si,0x731f
 mov di,0x9d42
 call _aspect_serial_directory_entry
 CHECK
 call _aspect_serial_directory_record
 CHECK
 call _aspect_serial_translation_policy
 CHECK
 mov ax,0xffee
 push ax
 call _aspect_serial_translate
 add sp,2
 CHECK
 mov ax,1
 jmp .done
.bad: xor ax,ax
.done:
 pop di
 pop si
 pop bp
 pop bx
 ret
_probe_reads: call far probe_reads_far
 ret
_probe_reset: call far probe_reset_far
 ret
SEGMENT _TEXT public class=_OVLCODE use16
probe_reads_far: mov ax,[cs:reads]
 retf
probe_reset_far: mov word [cs:reads],0
 retf
reads: dw 0
global __OvlRead___
__OvlRead___:
 inc word [cs:reads]
 push si
 push ds
 mov ds,cx
 mov si,dx
 xchg ax,bx
 mov dx,ax
 mov cx,si
 mov ah,0x3f
 int 0x21
 sbb dx,dx
 pop ds
 pop si
 ret
''')
    sources=[ROOT/'src/aspect/serial.c',ROOT/'src/aspect/serial_bank.asm',ROOT/'src/aspect/serial_bank.inc',
        ROOT/'src/aspect/serial_backend.asm',ROOT/'reconstruction/uart/core.asm',ROOT/'src/uart/api.asm',
        ROOT/'reconstruction/directory_accounting/patch.asm']
    root_objects=[];bank_objects=[]
    def assemble(source,name,defines=(),bank=False):
        obj=out/(name+'.obj')
        subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',
            '-I'+str(ROOT/'src/aspect')+'/',*['-D'+d for d in defines],str(source),'-o',str(obj)],check=True)
        (bank_objects if bank else root_objects).append(obj.name)
    for source in sources[3:-1]:assemble(source,source.stem,('UART_OMF',) if source.name=='core.asm' else ())
    assemble(sources[1],'serial-root',('ASPECT_SERIAL_OVERLAY_READY','SERIAL_BANK_ROOT_ONLY'))
    assemble(sources[1],'serial-overlay',('ASPECT_SERIAL_OVERLAY_READY','SERIAL_BANK_OVERLAY_ONLY'),bank=True)
    assemble(out/'reference.asm','reference',bank=True)
    read=(out/'read.asm').read_text();split=read.index('SEGMENT _TEXT public class=_OVLCODE')
    (out/'read-root.asm').write_text(read[:split]+'extern probe_reads_far,probe_reset_far\n')
    (out/'read-loader.asm').write_text('BITS 16\nCPU 8086\nglobal probe_reads_far,probe_reset_far\n'+read[split:])
    assemble(out/'read-root.asm','read-root');assemble(out/'read-loader.asm','read-loader')
    flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we']
    subprocess.run(['wcc',*flags,'-dASPECT_SERIAL_OVERLAY_READY',*['-d'+a+'='+b for a,b in aliases.items()],
        '-nt=ASIO_CODE','-nc=FARCODE','-fo=serial.obj',str(sources[0])],cwd=out,check=True)
    subprocess.run(['wcc',*flags,'-i='+str(ROOT/'src/aspect'),'-fo=probe.obj','probe.c'],cwd=out,check=True)
    # Reference and eviction code must be separate objects for sibling sections.
    ref=(out/'reference.asm').read_text();split=ref.index('SEGMENT EVICT_CODE')
    (out/'evict.asm').write_text('BITS 16\nCPU 8086\n'+ref[split:]);(out/'reference.asm').write_text(ref[:split])
    subprocess.run(['nasm','-fobj','reference.asm','-o','reference.obj'],cwd=out,check=True)
    subprocess.run(['nasm','-fobj','evict.asm','-o','evict.obj'],cwd=out,check=True)
    (out/'link.lnk').write_text('system dos\noption quiet\noption standard\noption stack=8192\noption map=PROBE.map\nname PROBE.EXE\nfile probe.obj,'+','.join(root_objects)+'\nbegin\nsection\nfile serial.obj,'+','.join(bank_objects)+'\nsection\nfile evict.obj\nend\n')
    subprocess.run(['wlink','@link.lnk'],cwd=out,check=True)
    subprocess.run(['wcl',*flags,'-k8192','-i='+str(ROOT/'src/aspect'),'-fe=PARENT.EXE','parent.c'],cwd=out,check=True)
    listing=(out/'PROBE.map').read_text()
    assert 'section 1 : _reference_translate' in listing and 'section 2 : _evict_asio' in listing
    assert not any(re.search(r'section \d+ : _aspect_serial_'+name+r'\s*$',listing,re.M) for name in hot)
    cases=[]
    for version,mode in [(1,0),(2,0),(2,1),(2,2)]:
        folder=out/f'v{version}-mode{mode}';folder.mkdir()
        server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(45)
        wire=bytearray();errors=[]
        def peer():
            try:
                conn,_=server.accept()
                with conn:
                    conn.settimeout(45);sent=False
                    while True:
                        data=conn.recv(4096)
                        if not data:break
                        wire.extend(data)
                        if b'D' in wire and not sent:conn.sendall(bytes([0,0x1a,0x80,0xff,0xff,0x80]));sent=True
            except OSError as error:errors.append(str(error))
        thread=threading.Thread(target=peer);thread.start()
        (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[serial]\nserial1=nullmodem server:127.0.0.1 port:'+str(server.getsockname()[1])+' transparent:1 rxdelay:200 txdelay:1\nserial2=disabled\nserial3=disabled\nserial4=disabled\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nmount d "'+str(folder)+'"\nc:\nPARENT '+str(version)+' '+str(mode)+' >d:\\RESULT.TXT\nif errorlevel 1 goto fail\necho PASS>d:\\PASS.TXT\ngoto done\n:fail\necho FAIL>d:\\FAIL.TXT\n:done\nexit\n')
        try:
            with (folder/'dosbox.log').open('w') as log:
                result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=out,
                    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=90)
        finally:
            server.close();thread.join(50)
        (folder/'serial.bin').write_bytes(wire)
        report=(folder/'RESULT.TXT').read_text()
        checks=dict(DOS_exit=result.returncode==0,passed=(folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),
            handback=report=='child=0 returned=1 status=0 count=2 raw=255,128\n',wire=bytes(wire)==b'D',peer=not errors and not thread.is_alive())
        cases.append(dict(version=version,mode=mode,passed=all(checks.values()),checks=checks,report=report,errors=errors,
            C_ASM_WORD_comparisons=5*65536,hot_reads_after_sibling_eviction=5*65536+35,register_canary_calls=20,loader_read_counter_positive_controls=2,loader_reads_during_hot_phase=0 if checks['passed'] else None))
        (out/'result.json').write_text(json.dumps(dict(passed=all(row['passed'] for row in cases),cases=cases),indent=2)+'\n')
        assert all(checks.values()),cases[-1]
    dependencies=[Path(__file__).resolve(),Path(original.__file__),*sources,ROOT/'src/aspect/serial.h',ROOT/'src/aspect/serial_handoff.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc']
    record=dict(passed=True,cases=cases,cpu='8086',probe_sha256=sha(out/'PROBE.EXE'),parent_sha256=sha(out/'PARENT.EXE'),
        source_hashes={str(path.relative_to(ROOT)):sha(path) for path in dependencies},
        generated_hashes={name:sha(out/name) for name in ('parent.c','probe.c','reference.asm','evict.asm','read.asm','read-root.asm','read-loader.asm','link.lnk')},
        original_inputs=[],physical_verified=False,scope=__doc__)
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS hot serial actual8086 DOS',len(cases),'cases')


if __name__=='__main__':main()
