; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_spawn_extension
extern program_get_ds
extern program_getenv
extern program_environment_tail
extern program_exec
extern program_service_85fc
extern program_service_9286
extern program_service_92a4
extern program_errno
extern program_comspec_name2
extern program_fallback_environment
extern program_state_e462
extern program_state_e45e
extern program_state_e460
%define short
%else
ORG 0x684a
%define program_get_ds 0x76b0
%define program_getenv 0x8e12
%define program_environment_tail 0x65ca
%define program_exec 0x6a22
%define program_service_85fc 0x85fc
%define program_service_9286 0x9286
%define program_service_92a4 0x92a4
%define program_errno 0x7b1c
%define program_comspec_name2 0x5e18
%define program_fallback_environment 0x9062
%define program_state_e462 0xe462
%define program_state_e45e 0xe45e
%define program_state_e460 0xe460
%endif
%include "encodings.inc"
program_spawn_extension:
L_684a: push bp
L_684b: mov_load bp,sp
L_684d: sub sp,0x84
L_6851: push di
L_6852: push si
L_6853: cmp word [bp+0xc],0x0
L_6857: jnz short L_6877
L_6859: mov si,[bp+0x6]
L_685c: mov_load di,si
L_685e: mov ax,program_comspec_name2
L_6861: push ax
L_6862: call program_getenv
L_6865: pop bx
L_6866: mov_load si,ax
L_6868: or_load si,si
L_686a: jnz short L_687c
L_686c: mov word [program_errno],0x8
L_6872: mov ax,0xffff
L_6875: jmp short L_68e8
L_6877: sub_load di,di
L_6879: mov si,[bp+0x6]
L_687c: push di
L_687d: sub_load ax,ax
L_687f: push ax
L_6880: lea ax,[bp-0x84]
L_6884: push ax
L_6885: lea ax,[bp-0x4]
L_6888: push ax
L_6889: lea ax,[bp-0x2]
L_688c: push ax
L_688d: push word [bp+0xa]
L_6890: push word [bp+0x8]
L_6893: call program_environment_tail
L_6896: add sp,0xe
L_6899: inc ax
L_689a: jz short L_6872
L_689c: push word [bp-0x4]
L_689f: lea ax,[bp-0x84]
L_68a3: push ax
L_68a4: push si
L_68a5: push word [bp+0x4]
L_68a8: call program_exec
L_68ab: add sp,0x8
L_68ae: mov_load di,ax
L_68b0: cmp word [bp-0x2],program_fallback_environment
L_68b5: jnz short L_68df
L_68b7: push word [program_state_e462]
L_68bb: mov ax,program_fallback_environment
L_68be: push ax
L_68bf: call program_get_ds
L_68c2: push ax
L_68c3: push word [program_state_e45e]
L_68c7: push word [program_state_e460]
L_68cb: call program_service_9286
L_68ce: add sp,0xa
L_68d1: push word [program_state_e460]
L_68d5: push word [program_state_e45e]
L_68d9: call program_service_85fc
L_68dc: pop bx
L_68dd: jmp short L_68e5
L_68df: push word [bp-0x2]
L_68e2: call program_service_92a4
L_68e5: pop bx
L_68e6: mov_load ax,di
L_68e8: pop si
L_68e9: pop di
L_68ea: mov_load sp,bp
L_68ec: pop bp
L_68ed: ret
