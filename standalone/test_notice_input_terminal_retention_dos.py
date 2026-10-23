#!/usr/bin/env python3
"""Unrepaired child INT33 owner through the ordinary complete DOS terminal.

The owned observer replaces INT33 after identifying the real child callback.
Its default case restores saved driver/vector only after both products return;
the optional repair case restores the vector at the child's DOS31 boundary.
No application binary or product state is patched.
"""
import argparse,json,re,shutil,struct,subprocess,sys
from pathlib import Path
import test_aspect_renderer_dos as render
from test_aspect_parent_process_dos import prepare_observer
from notice_input_fault_probe import instrument as child_probe,WORDS as CHILD_WORDS
from directory_fixtures import directory,prm

ROOT=render.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

WORDS=['vector_off','vector_seg','injected','child_exit_ax','parent_exit_ax',
       'child_mcb_owner','parent_mcb_owner','vector_untouched','parent_status',
       'raw_child_status','driver_equal','repair_applied']

def instrument(source,child_map,offsets,repair):
    source=child_probe(source,child_map)
    marker=' mov word [cs:nip_seen],1\n'
    assert source.count(marker)==1
    source=source.replace(marker,marker+''' mov ax,0x3533
 int 0x21
 mov [cs:ret_vector_off],bx
 mov [cs:ret_vector_seg],es
 push ds
 push cs
 pop ds
 mov dx,ret_foreign
 mov ax,0x2533
 int 0x21
 pop ds
 inc word [cs:ret_injected]
''')
    # The standard observer only recognizes DOS4C. Accept DOS31 for its
    # existing child-result snapshot, and separately sample both real exits.
    marker='.exit_check:\n'
    assert source.count(marker)==1
    source=source.replace(marker,marker+' call ret_exit\n')
    marker=' cmp byte [ss:bp+17],0x4c\n jne .chain\n'
    assert source.count(marker)==1
    source=source.replace(marker,''' cmp byte [ss:bp+17],0x31
 je .retained_child
 cmp byte [ss:bp+17],0x4c
 jne .chain
.retained_child:
''')
    # Collection executes after the terminal returned to DOS. Restore only
    # test-owned state then, never during either product's recovery attempt.
    marker=' mov ax,[es:old1c]\n'
    assert source.count(marker)==1
    source=source.replace(marker,''' call ret_collect
'''+marker)
    code='''
ret_foreign:
 iret
ret_exit:
 cmp byte [ss:bp+17],0x31
 je .sample
 cmp byte [ss:bp+17],0x4c
 jne .done
.sample:
 mov ah,0x62
 int 0x21
 cmp bx,[cs:nip_child_psp]
 jne .parent
 mov ax,[ss:bp+16]
 mov [cs:ret_child_exit_ax],ax
 CHILD_REPAIR
 jmp .done
.parent:
 cmp bx,[cs:parent_psp]
 jne .done
 mov ax,[ss:bp+16]
 mov [cs:ret_parent_exit_ax],ax
 mov es,[cs:parent_ds]
 mov ax,[es:PARENT_STATUS]
 mov [cs:ret_parent_status],ax
 mov ax,[es:PARENT_RESULT+4]
 mov [cs:ret_raw_child_status],ax
 mov ax,0x3533
 int 0x21
 cmp bx,ret_foreign
 jne .done
 mov ax,es
 push cs
 pop bx
 cmp ax,bx
 jne .done
 inc word [cs:ret_vector_untouched]
.done:
 ret
ret_collect:
 push ax
 push bx
 push dx
 push ds
 push es
 mov bx,[es:nip_child_psp]
 dec bx
 push es
 mov es,bx
 mov ax,[es:1]
 pop es
 mov [es:ret_child_mcb_owner],ax
 mov bx,[es:parent_psp]
 dec bx
 push es
 mov es,bx
 mov ax,[es:1]
 pop es
 mov [es:ret_parent_mcb_owner],ax
 mov dx,[es:ret_vector_off]
 mov ds,[es:ret_vector_seg]
 mov ax,0x2533
 int 0x21
 ; Restore snapshot captured by the independent parent probe at startup.
 mov dx,mouse_before
 mov ax,0x17
 int 0x33
 mov dx,mouse_after
 mov ax,0x16
 int 0x33
 push ds
 push es
 pop ds
 mov si,mouse_before
 mov di,mouse_after
 mov cx,[mp_state_bytes]
 or cx,cx
 jz .different
 cmp cx,2048
 ja .different
 cld
 repe cmpsb
 jne .different
 mov word [ret_driver_equal],1
.different:
 pop ds
 pop es
 pop ds
 pop dx
 pop bx
 pop ax
 ret
'''.replace('PARENT_STATUS',str(offsets['terminal_program_status'])).replace('PARENT_RESULT',str(offsets['terminal_program_result']))
    code=code.replace('CHILD_REPAIR','''push ds
 mov dx,[cs:ret_vector_off]
 mov ds,[cs:ret_vector_seg]
 mov ax,0x2533
 int 0x21
 pop ds
 inc word [cs:ret_repair_applied]''' if repair else '')
    source=source.replace('resident_end:',code+'\nresident_end:')
    source=source.replace('sample_end:',''.join('ret_'+n+': dw 0\n' for n in WORDS)+'sample_end:')
    # Both products intentionally retain most conventional memory. Keep the
    # collector resident and enter it with a tiny second COM rather than
    # requiring DOS to load another complete observer image after DOS31.
    source=source[:source.index('\ncollect:')].replace('resident_end:','')+'''
collect:
 cmp bx,handler
 jne failed
 cmp word [es:magic],0x524e
 jne failed
 call ret_collect
 push ds
 mov dx,[old21]
 mov ds,[old21+2]
 mov ax,0x2521
 int 0x21
 pop ds
 push ds
 mov dx,[old1c]
 mov ds,[old1c+2]
 mov ax,0x251c
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,sample
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,sample_end-sample
 jne failed
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\\RENDER.BIN',0
resident_end:
 dw collect
'''
    return source

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--label',required=True)
    ap.add_argument('--repair-on-child-exit',action='store_true');ap.add_argument('--port',type=int,choices=[1,2],default=1)
    args=ap.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/notice-input-terminal-retention'/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE'
    child=ROOT/'build/aspect-notice-input-parent/ASPECT.EXE'
    sources={}
    for product in (parent,child):
        m=json.loads((product.parent/'manifest.json').read_text());assert m['binary_sha256']==render.sha(product)
        for n,h in m['sources'].items():
            assert n not in sources or sources[n]==h
            assert render.sha(ROOT/n)==h
            sources[n]=h
        for path in [product.parent/'manifest.json',product.parent/('terminal.map' if product==parent else 'ASPECT.map')]:
            sources[str(path.relative_to(ROOT))]=render.sha(path)
    for name in ['standalone/test_notice_input_terminal_retention_dos.py','standalone/test_aspect_parent_process_dos.py','standalone/test_aspect_renderer_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/mouse_parent_probe.py','standalone/notice_input_fault_probe.py','standalone/notice_input_parent_probe.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','src/aspect/compiler.py']:
        sources[name]=render.sha(ROOT/name)
    for name,h in sources.items():
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out;offsets=render.map_offsets(parent.parent/'terminal.map')
    prepare_observer(out,offsets,parent.parent/'terminal.map',sound_probe=True,mouse_probe=True)
    source=instrument((out/'observer.asm').read_text(),child.parent/'ASPECT.map',offsets,args.repair_on_child_exit)
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True)
    collect=struct.unpack('<H',(out/'RENDER.COM').read_bytes()[-2:])[0]
    (out/'fetch.asm').write_text('BITS 16\nCPU 8086\nORG 100h\nmov ax,0x3521\nint 0x21\npush es\npop ds\npush es\nmov ax,'+str(collect)+'\npush ax\nretf\n')
    subprocess.run(['nasm','-fbin',str(out/'fetch.asm'),'-o',str(out/'FETCH.COM')],check=True)
    folder=out/'unrepaired';folder.mkdir()
    for product in (parent,child):shutil.copyfile(product,folder/product.name)
    harness=render.adapter(cpu='8086',observer_collector='FETCH');harness.BINARY=folder/'TERMINAL.EXE'
    script='proc main\nwaitfor "LOGIN:" 5\nputenv "PATH="\nrun "ABSENT.COM"\ntransmit "BAD-CONTINUED"\nendproc\n'
    payload=bytearray(directory(port=args.port));payload[302:311]=b'LOGIN\0\0\0\0'
    settings=bytearray(prm(port=args.port,soft=0,hard=1));struct.pack_into('<HH',settings,0x4e4,8,4)
    files={'LOGIN.ASX':compile_source(script),'RENDER.COM':(out/'RENDER.COM').read_bytes(),'FETCH.COM':(out/'FETCH.COM').read_bytes()}
    result=harness.run('unrepaired','success','p9000 space p1000 r e a d y p500 a-x',expected=0 if args.repair_on_child_exit else 14,com=args.port,directory=bytes(payload),prm=bytes(settings),
        arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',files=files,
        banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:',working_drive='d',observer='RENDER')
    raw=(folder/'RENDER.BIN').read_bytes();tail=struct.unpack_from('<'+str(len(WORDS))+'H',raw,len(raw)-2*len(WORDS));w=dict(zip(WORDS,tail))
    base=raw[:-len(WORDS)*2];c=dict(zip(CHILD_WORDS,struct.unpack_from('<'+str(len(CHILD_WORDS))+'H',base,len(base)-2*len(CHILD_WORDS))))
    header=struct.unpack_from('<7H',raw);screen=(folder/'SCREEN.BIN').read_bytes()[::2];wire=(folder/'serial.bin').read_bytes()
    result['checks'].update(injection_observed=w['injected']==c['seen']==1,
        child_binary_unchanged=render.sha(child)==render.sha(folder/'ASPECT.EXE'),
        child_retained=w['child_exit_ax']==0x310a and w['child_mcb_owner']==c['child_psp'],
        terminal_exit_policy=(w['parent_exit_ax']==0x4c00 if args.repair_on_child_exit else w['parent_exit_ax']==0x310e and w['parent_mcb_owner']==header[5]),
        foreign_vector_policy=w['vector_untouched']==int(not args.repair_on_child_exit),
        raw_retained_child_status=w['raw_child_status']==0x030a and w['parent_status']==5,
        owned_driver_cleanup=w['driver_equal']==1,
        repair_policy=w['repair_applied']==int(args.repair_on_child_exit),
        typed_input_failure=c['notice_cause']==11,
        terminal_reported_retention=b'ASPECT memory retained.' in screen and (b'Mouse restore failed' in screen)==(not args.repair_on_child_exit),
        continued_terminal=(b'ready' in wire)==args.repair_on_child_exit,
        no_script_continuation=b'BAD-CONTINUED' not in wire)
    assert all(render.sha(ROOT/n)==h for n,h in sources.items())
    result.update(passed=all(result['checks'].values()),retention=w,child_input=c,header=header,sources=sources,repair_on_child_exit=args.repair_on_child_exit,port=args.port,
        parent_sha256=render.sha(parent),child_sha256=render.sha(child),observer_sha256=render.sha(out/'RENDER.COM'),
        scope=__doc__+' Optional owned vector repair occurs at the child DOS31 boundary, after its final cleanup decision, before terminal resume. This does not repair/reuse/unload the retained child. DOSBox-X8086 modeled Hayes connection; retained blocks remain until the private VM ends. No physical modem, general unload or full application acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FINAL', 'PASS' if result['passed'] else 'FAIL',w,c,flush=True)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
