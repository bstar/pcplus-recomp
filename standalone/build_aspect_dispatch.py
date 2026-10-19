#!/usr/bin/env python3
"""Original-free flat/OMF recovery and linked8086 DOS dispatcher diagnostic.

Source-owned callbacks deliberately stand in for the interpreter, CRT and UI.
This diagnostic does not compile scripts or implement opcode handlers.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-dispatch'
SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
START, END = 0x4b1f, 0x4bff
NATIVE = {
    'initialize': 0xc1d7, 'probe': 0x9048, 'open': 0xc21f,
    'service': 0x4de9, 'read': 0x4cb4, 'seek': 0x853a,
    'wait': 0x4c3c, 'error': 0x4efb, 'invalid_command': 0x4f88,
    'shutdown': 0x4bff, 'cleanup': 0xc2eb, 'close': 0x8318, 'finish': 0xc273,
}
DATA = {'argument': 0xe3ac, 'paused': 0x8e20, 'wait_disabled': 0xe382,
        'seek_enabled': 0xe2f8, 'stream': 0x4b02, 'handlers': 0x4b08,
        'exit_state': 0xe378, 'next_script': 0xe104}

ASM = r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_dispatch
global _aspect_test
_aspect_test:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,ds
 mov es,ax
 mov di,_result
 xor ax,ax
 mov cx,16
 rep stosw
 mov ax,[bp+4]
 mov [opcode],ax
 mov ax,[bp+6]
 mov [mode],ax
 mov word [aspect_dispatch_exit_state],0
 mov word [aspect_dispatch_paused],0
 mov word [aspect_dispatch_seek_enabled],0
 mov word [aspect_dispatch_wait_disabled],0
 mov word [stream_record+6],0
 test ax,8
 jz .notpaused
 mov word [aspect_dispatch_paused],1
.notpaused:
 test ax,16
 jz .notdisabled
 mov word [aspect_dispatch_wait_disabled],1
.notdisabled:
 test ax,32
 jz .notseek
 mov word [aspect_dispatch_seek_enabled],1
.notseek:
 test ax,64
 jz .noteof
 mov word [stream_record+6],0x10
.noteof:
 mov si,0x1111
 mov di,0x2222
 mov [saved_sp],sp
 mov ax,0x1234
 push ax
 push word [bp+8]
 call aspect_dispatch
 cmp sp,[saved_sp]
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
 inc word [_result+30]
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
'''

# Counters: initialize/probe/open/service/read/seek/wait/error/invalid/
# shutdown/cleanup/close/finish/handler/bad_callback_arg/bad_native_abi.
ASM += '\n'.join('global aspect_dispatch_'+name for name in NATIVE) + '\n'
ASM += r'''
aspect_dispatch_initialize:
 inc word [_result]
 ret
aspect_dispatch_probe:
 inc word [_result+2]
 push bp
 mov bp,sp
 cmp word [bp+4],aspect_dispatch_argument
 je .argok
 inc word [_result+28]
.argok:
 mov word [aspect_dispatch_exit_state],0
 mov ax,[mode]
 and ax,1
 pop bp
 ret
aspect_dispatch_open:
 inc word [_result+4]
 push bp
 mov bp,sp
 mov ax,[bp+4]
 cmp ax,di
 jne .bad
 mov ax,[bp+6]
 cmp ax,si
 je .ok
.bad:
 inc word [_result+28]
.ok:
 mov ax,[mode]
 and ax,2
 pop bp
 ret 4
aspect_dispatch_service:
 inc word [_result+6]
 mov ax,[mode]
 and ax,4
 ret
aspect_dispatch_read:
 inc word [_result+8]
 mov ax,[opcode]
 ret
aspect_dispatch_seek:
 inc word [_result+10]
 push bp
 mov bp,sp
 cmp word [bp+4],stream_record
 jne .bad
 cmp word [bp+6],0xffff
 jne .bad
 cmp word [bp+8],0xffff
 jne .bad
 cmp word [bp+10],1
 je .ok
.bad:
 inc word [_result+28]
.ok:
 pop bp
 ret
aspect_dispatch_wait:
 inc word [_result+12]
 push bp
 mov bp,sp
 cmp word [bp+4],0
 je .ok
 inc word [_result+28]
.ok:
 cmp word [_result+12],2
 jb .keepwaiting
 mov word [aspect_dispatch_paused],0
.keepwaiting:
 pop bp
 ret 2
aspect_dispatch_error:
 inc word [_result+14]
 push bp
 mov bp,sp
 cmp word [bp+4],0x6b
 je .ok
 inc word [_result+28]
.ok:
 mov word [aspect_dispatch_exit_state],1
 pop bp
 ret 2
aspect_dispatch_invalid_command:
 inc word [_result+16]
 mov word [aspect_dispatch_exit_state],1
 ret
aspect_dispatch_shutdown:
 inc word [_result+18]
 ret
aspect_dispatch_cleanup:
 inc word [_result+20]
 ret
aspect_dispatch_close:
 inc word [_result+22]
 push bp
 mov bp,sp
 cmp word [bp+4],stream_record
 je .ok
 inc word [_result+28]
.ok:
 pop bp
 ret
aspect_dispatch_finish:
 inc word [_result+24]
 ret
handler:
 inc word [_result+26]
 mov word [aspect_dispatch_exit_state],1
 test word [mode],128
 jz .done
 cmp word [_result+26],1
 jne .done
 mov word [aspect_dispatch_exit_state],999
.done:
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
'''
ASM += '\n'.join('global aspect_dispatch_'+name for name in DATA) + '\n'
ASM += r'''
global _result
_result: times 16 dw 0
opcode: dw 0
mode: dw 0
saved_sp: dw 0
aspect_dispatch_argument: times 8 db 0
aspect_dispatch_paused: dw 0
aspect_dispatch_wait_disabled: dw 0
aspect_dispatch_seek_enabled: dw 0
aspect_dispatch_stream: dw stream_record
aspect_dispatch_handlers: times 215 dw handler
aspect_dispatch_exit_state: dw 0
aspect_dispatch_next_script: dw 0x5678
stream_record: times 8 db 0
'''

C = r'''
#include <stdio.h>
extern unsigned result[16];
extern void aspect_test(unsigned opcode,unsigned flags,unsigned owner);
static unsigned checks,failures;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL %u\n",checks);}}
static void common(unsigned probe,unsigned open,unsigned service,unsigned read,unsigned seek,
                   unsigned wait,unsigned error,unsigned invalid,unsigned shutdown,unsigned close,unsigned handler){
 ck(result[0]==1);ck(result[1]==probe);ck(result[2]==open);ck(result[3]==service);
 ck(result[4]==read);ck(result[5]==seek);ck(result[6]==wait);ck(result[7]==error);
 ck(result[8]==invalid);ck(result[9]==shutdown);ck(result[10]==close);ck(result[11]==close);
 ck(result[12]==1);ck(result[13]==handler);ck(result[14]==0);ck(result[15]==0);
}
int main(void){unsigned i;FILE *f;
 for(i=0;i<215;++i){aspect_test(i,1,0);common(1,0,1,1,0,0,0,0,1,1,1);}
 aspect_test(7,2,1);common(1,1,1,1,0,0,0,0,0,1,1);
 aspect_test(7,0,0);common(1,1,0,0,0,0,0,0,0,0,0);
 aspect_test(7,5,0);common(1,0,1,0,0,0,0,0,1,1,0);
 aspect_test(7,9,0);common(1,0,1,1,0,2,0,0,1,1,1);
 aspect_test(7,41,0);common(1,0,2,2,1,2,0,0,1,1,1);
 aspect_test(7,25,0);common(1,0,1,1,0,0,0,0,1,1,1);
 aspect_test(0xc7,9,0);common(1,0,1,1,0,0,0,0,1,1,1);
 aspect_test(0xd7,1,0);common(1,0,1,1,0,0,0,1,1,1,0);
 aspect_test(0xffff,65,0);common(1,0,1,1,0,0,1,0,1,1,0);
 aspect_test(7,129,0);common(2,0,2,2,0,0,0,0,1,2,2);
 aspect_test(7,129,1);common(2,0,2,2,0,0,0,0,1,2,2);
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_DISPATCH %u checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_DISPATCH %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/aspect/dispatch.asm'
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    subprocess.run(['nasm','-f','bin','-DASPECT_DISPATCH_FLAT',include,str(source),
                    '-o',str(OUT/'dispatch.bin'),'-l',str(OUT/'dispatch-flat.lst')],check=True)
    assert len((OUT/'dispatch.bin').read_bytes()) == END-START
    subprocess.run(['nasm','-f','obj',include,str(source),'-o',str(OUT/'dispatch.obj')],check=True)
    (OUT/'callbacks.asm').write_text(ASM)
    (OUT/'diagnostic.c').write_text(C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
                    '-fm=DISPATCH.map','-fe=DISPATCH.EXE',str(OUT/'diagnostic.c'),
                    str(OUT/'dispatch.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    inputs=[source,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
    report=dict(binary_sha256=sha((OUT/'DISPATCH.EXE').read_bytes()),
                flat_sha256=sha((OUT/'dispatch.bin').read_bytes()),native_start=START,native_end_exclusive=END,
                sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},original_inputs=[],
                scope='Exact recovered dispatcher only, source-owned callback backend; no opcode implementation or full VM')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
