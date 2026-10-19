#!/usr/bin/env python3
"""Compose real native dispatcher, abort and setjmp/longjmp in8086 DOS.

Only file/UI/handler callbacks are diagnostic models. Nonlocal control transfer
executes recovered source instructions, not a simulated return or stack reset.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/aspect-unwind'
UNITS = [
    ('dispatch','src/aspect/dispatch.asm','ASPECT_DISPATCH_FLAT',None,0x4b1f,0x4bff,0x5d1f),
    ('abort','src/aspect/abort.asm','ASPECT_ABORT_FLAT',None,0x4ebc,0x4efb,0x60bc),
    ('setjmp','reconstruction/transfer_session/setjmp.asm',None,'TRANSFER_SESSION_OMF',0x9048,0x9065,0xa248),
    ('longjmp','reconstruction/transfer_session/longjmp.asm',None,'TRANSFER_SESSION_OMF',0x9065,0x9086,0xa265),
    ('stack','src/aspect/value_stack.asm','ASPECT_STACK_FLAT',None,0xd0d0,0xd195,109184),
    ('copy','reconstruction/erase/move_bytes.asm',None,'ERASE_OMF',0x85b4,0x85fc,0x97b4),
]

ASM = r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_dispatch,aspect_abort,session_setjmp,aspect_stack_push_word
extern _fault_site,_owner,_restart,_show_position
global _unwind_run
_unwind_run:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [saved_sp],sp
 mov [saved_bp],bp
 mov si,0x1111
 mov di,0x2222
 mov ax,0x1234
 push ax
 push word [_owner]
 call aspect_dispatch
 cmp sp,[saved_sp]
 jne .bad
 cmp bp,[saved_bp]
 jne .bad
 cmp si,0x1111
 jne .bad
 cmp di,0x2222
 jne .bad
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 je .done
.bad:
 inc word [_calls+30]
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; This really tail-calls native setjmp. Longjmp returns directly to dispatcher.
global aspect_dispatch_probe
aspect_dispatch_probe:
 inc word [_calls+2]
 jmp session_setjmp

; Selected callbacks take a nested, deliberately nontrivial stack path.
maybe_abort:
 cmp ax,[_fault_site]
 jne .done
 cmp word [_restart],0
 je .abort
 cmp word [_calls+4],2
 jb .done
.abort:
 inc word [_calls+26]
 call nested_abort_a
 inc word [_calls+28]
.done:
 ret
nested_abort_a:
 push bp
 mov bp,sp
 sub sp,byte 14
 push si
 push di
 mov si,0xaaaa
 mov di,0xbbbb
 call nested_abort_b
 inc word [_calls+28]
 pop di
 pop si
 mov sp,bp
 pop bp
 ret
nested_abort_b:
 push bp
 mov bp,sp
 sub sp,byte 18
 mov si,0xcccc
 mov di,0xdddd
 call aspect_abort
 inc word [_calls+28]
 mov sp,bp
 pop bp
 ret

global aspect_dispatch_initialize,aspect_dispatch_open,aspect_dispatch_service
aspect_dispatch_initialize:
 inc word [_calls]
 mov word [aspect_dispatch_exit_state],0
 mov ax,[_show_position]
 mov [aspect_abort_display_position],ax
 ret
aspect_dispatch_open:
 push bp
 mov bp,sp
 inc word [_calls+4]
 mov ax,0x1234
 mov dx,[_owner]
 cmp word [_calls+4],1
 je .first
 mov ax,0x5678
 xor dx,dx
.first:
 cmp [bp+6],ax
 jne .bad
 cmp [bp+4],dx
 je .argsok
.bad:
 inc word [_calls+30]
.argsok:
 mov word [aspect_dispatch_exit_state],0
 mov ax,aspect_stack_arena+0x3aca-1
 mov [aspect_stack_pointer],ax
 mov byte [aspect_stack_arena+0x3aca-1],0xa5
 mov byte [aspect_stack_arena+0x3aca],0x5a
 mov word [stream_record+6],0x10
 cmp word [_fault_site],6
 jne .flagsok
 mov word [stream_record+6],0
.flagsok:
 mov word [aspect_dispatch_paused],0
 cmp word [_fault_site],7
 jne .notwait
 mov word [aspect_dispatch_paused],1
.notwait:
 mov ax,1
 call maybe_abort
 mov ax,1
 pop bp
 ret 4
aspect_dispatch_service:
 inc word [_calls+6]
 mov ax,2
 call maybe_abort
 xor ax,ax
 ret

global aspect_dispatch_read,aspect_dispatch_seek,aspect_dispatch_wait
aspect_dispatch_read:
 inc word [_calls+8]
 mov ax,3
 call maybe_abort
 mov ax,7
 cmp word [_fault_site],5
 jb .done
 cmp word [_fault_site],6
 ja .done
 mov ax,0xffff
.done:
 ret
aspect_dispatch_seek:
 inc word [_calls+30]
 ret
aspect_dispatch_wait:
 mov ax,7
 call maybe_abort
 mov word [aspect_dispatch_paused],0
 ret 2

global aspect_dispatch_error,aspect_dispatch_invalid_command
aspect_dispatch_error:
 inc word [_calls+10]
 push bp
 mov bp,sp
 cmp word [bp+4],107
 je .ok
 inc word [_calls+30]
.ok:
 mov ax,5
 call maybe_abort
 ; First script in a chain reaches here without raising its selected fault.
 mov word [aspect_dispatch_exit_state],999
 pop bp
 ret 2
aspect_dispatch_invalid_command:
 inc word [_calls+12]
 mov ax,6
 call maybe_abort
 mov word [aspect_dispatch_exit_state],999
 ret
handler:
 inc word [_calls+14]
 cmp word [_fault_site],8
 jne .ordinary
 ; A chained first script uses a valid push; the failing script overflows.
 cmp word [_restart],0
 je .overflow
 cmp word [_calls+4],1
 jne .overflow
 dec word [aspect_stack_pointer]
.overflow:
 mov ax,0x7b6c
 push ax
 call aspect_stack_push_word
.ordinary:
 mov ax,4
 call maybe_abort
 mov ax,1
 cmp word [_restart],0
 je .set
 cmp word [_calls+4],1
 jne .set
 mov ax,999
.set:
 mov [aspect_dispatch_exit_state],ax
 ret

global aspect_stack_error
aspect_stack_error:
 push bp
 mov bp,sp
 inc word [_stack_errors]
 cmp word [bp+4],105
 je .ok
 inc word [_calls+30]
.ok:
 mov ax,8
 call maybe_abort
 inc word [_calls+28]
 pop bp
 ret 2

global aspect_dispatch_shutdown,aspect_dispatch_cleanup,aspect_dispatch_close,aspect_dispatch_finish
aspect_dispatch_shutdown:
 inc word [_calls+16]
 ret
aspect_dispatch_cleanup:
 inc word [_calls+18]
 ret
aspect_dispatch_close:
 inc word [_calls+20]
 push bp
 mov bp,sp
 cmp word [bp+4],stream_record
 je .ok
 inc word [_calls+30]
.ok:
 pop bp
 ret
aspect_dispatch_finish:
 inc word [_calls+22]
 ret

global aspect_abort_tell,aspect_abort_format,aspect_abort_print
aspect_abort_tell:
 inc word [_position_calls]
 push bp
 mov bp,sp
 cmp word [bp+4],stream_record
 je .ok
 inc word [_calls+30]
.ok:
 mov ax,0x2345
 mov dx,1
 pop bp
 ret
aspect_abort_format:
 inc word [_position_calls+2]
 push bp
 mov bp,sp
 cmp word [bp+6],aspect_abort_format_string
 jne .bad
 cmp word [bp+8],0x2345
 jne .bad
 cmp word [bp+10],1
 je .ok
.bad:
 inc word [_calls+30]
.ok:
 mov bx,[bp+4]
 mov word [bx],0x4f50
 mov word [bx+2],0x0053
 pop bp
 ret
aspect_abort_print:
 inc word [_position_calls+4]
 cmp word [bx],0x4f50
 jne .bad
 cmp word [bx+2],0x0053
 je .done
.bad:
 inc word [_calls+30]
.done:
 ret

SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_dispatch_argument,aspect_dispatch_paused,aspect_dispatch_wait_disabled
 global aspect_dispatch_seek_enabled,aspect_dispatch_stream,aspect_dispatch_handlers
 global aspect_dispatch_exit_state,aspect_dispatch_next_script
 global aspect_abort_display_position,aspect_abort_format_string
 global _calls,_position_calls,_context_guard,_exit_state
 global aspect_stack_pointer,aspect_stack_arena,_stack_pointer,_stack_arena,_stack_errors
_calls: times 16 dw 0
_position_calls: times 3 dw 0
_context_guard: dw 0xa55a
aspect_dispatch_argument: times 10 db 0
 dw 0x5aa5
aspect_dispatch_paused: dw 0
aspect_dispatch_wait_disabled: dw 0
aspect_dispatch_seek_enabled: dw 0
aspect_dispatch_stream: dw stream_record
aspect_dispatch_handlers: times 215 dw handler
aspect_dispatch_exit_state:
_exit_state: dw 0
aspect_dispatch_next_script: dw 0x5678
aspect_abort_display_position: dw 0
aspect_abort_format_string: db 'owned position diagnostic',0
saved_sp: dw 0
saved_bp: dw 0
stream_record: times 6 db 0
 dw 0x10
_stack_errors: dw 0
aspect_stack_pointer:
_stack_pointer: dw 0
aspect_stack_arena:
_stack_arena: times 0x3aca db 0xa5
 db 0x5a
'''

C = r'''
#include <stdio.h>
#include <string.h>
extern unsigned calls[16],position_calls[3],context_guard[7],exit_state;
extern unsigned stack_pointer,stack_errors;
extern unsigned char stack_arena[0x3aca+1];
extern void unwind_run(void);
unsigned fault_site,owner,restart,show_position;
static unsigned checks,failures,cases;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL site=%u owner=%u chain=%u position=%u check=%u\n",fault_site,owner,restart,show_position,checks);}}
static void run(void){
 unsigned scripts=restart?2:1,aborting=fault_site!=0;
 memset(calls,0,sizeof(calls));memset(position_calls,0,sizeof(position_calls));
 stack_errors=0;
 ++cases;unwind_run();
 ck(calls[0]==1);ck(calls[1]==scripts);ck(calls[2]==scripts);
 ck(calls[8]==(!owner||restart));ck(calls[9]==scripts);ck(calls[10]==scripts);
 ck(calls[11]==1);ck(calls[13]==aborting);ck(calls[14]==0);ck(calls[15]==0);
 ck(exit_state==(aborting?0xffff:1));
 ck(context_guard[0]==0xa55a);ck(context_guard[6]==0x5aa5);
 ck(context_guard[2]==(restart?0:owner));ck(context_guard[3]==(restart?0x5678:0x1234));
 ck(context_guard[1]!=0);ck(context_guard[4]!=0);ck(context_guard[5]!=0);
 ck(position_calls[0]==(aborting&&show_position));
 ck(position_calls[1]==(aborting&&show_position));
 ck(position_calls[2]==(aborting&&show_position));
 ck(stack_errors==(fault_site==8));
 if(fault_site==8){ck(stack_pointer==(unsigned)stack_arena+0x3aca-1);ck(stack_arena[0x3aca-1]==0xa5);ck(stack_arena[0x3aca]==0x5a);}
 if(fault_site==1){ck(calls[3]==(restart?1:0));ck(calls[4]==(restart?1:0));}
 else {ck(calls[3]==scripts);ck(calls[4]==(fault_site==2?(restart?1:0):scripts));}
 if(fault_site==5)ck(calls[5]==scripts);else ck(calls[5]==0);
 if(fault_site==6)ck(calls[6]==scripts);else ck(calls[6]==0);
 if(fault_site>=1&&fault_site<=3)ck(calls[7]==(restart?1:0));
 else if(fault_site==5||fault_site==6)ck(calls[7]==0);
 else if(fault_site==7)ck(calls[7]==(restart?1:0));
 else ck(calls[7]==scripts);
}
int main(void){FILE *f;
 for(fault_site=0;fault_site<=8;++fault_site)
  for(owner=0;owner<=1;++owner)
   for(restart=0;restart<=1;++restart)
    for(show_position=0;show_position<=1;++show_position)run();
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_UNWIND %u cases %u checks %u failures\n",cases,checks,failures);fclose(f);
 printf("ASPECT_UNWIND %u cases %u checks %u failures\n",cases,checks,failures);
 return failures?1:0;
}
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    include='-I'+str(ROOT/'reconstruction/uart')+'/'
    objects=[];inputs=[Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc']
    native=[]
    for name,rel,flat_define,obj_define,start,end,file_start in UNITS:
        source=ROOT/rel;inputs.append(source)
        flat=OUT/(name+'.bin');obj=OUT/(name+'.obj')
        subprocess.run(['nasm','-f','bin',include]+(['-D'+flat_define] if flat_define else [])+
                       [str(source),'-o',str(flat)],check=True)
        subprocess.run(['nasm','-f','obj',include]+(['-D'+obj_define] if obj_define else [])+
                       [str(source),'-o',str(obj)],check=True)
        assert flat.stat().st_size==end-start
        native.append(dict(name=name,source=rel,cs_start=start,cs_end_exclusive=end,
                           file_start=file_start,bytes=end-start,flat_sha256=sha(flat)))
        objects.append(str(obj))
    (OUT/'callbacks.asm').write_text(ASM);(OUT/'diagnostic.c').write_text(C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
                    '-fm=UNWIND.map','-fe=UNWIND.EXE',str(OUT/'diagnostic.c'),*objects,
                    str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    result=dict(binary_sha256=sha(OUT/'UNWIND.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        native_units=native,original_inputs=[],
        scope='Real recovered dispatcher/abort/setjmp/longjmp composition; diagnostic file/UI/opcode callbacks. Not a complete VM or real resource owner.')
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
