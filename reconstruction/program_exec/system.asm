; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_system
extern program_getenv
extern program_spawnv
extern program_spawn_search
extern program_access
extern program_environ
extern program_errno
extern program_comspec_name
extern program_switch_c
extern program_default_shell
%define short
%else
ORG 0x896a
%define program_getenv 0x8e12
%define program_spawnv 0x68ee
%define program_spawn_search 0xa4a6
%define program_access 0x93aa
%define program_environ 0x7b43
%define program_errno 0x7b1c
%define program_comspec_name 0x7ae8
%define program_switch_c 0x7af0
%define program_default_shell 0x7af3
%endif
%include "encodings.inc"
program_system:
L_896a: push bp
L_896b: mov_load bp,sp
L_896d: sub sp,0xc
L_8970: mov ax,program_comspec_name
L_8973: push ax
L_8974: call program_getenv
L_8977: add sp,0x2
L_897a: mov [bp-0x8],ax
L_897d: cmp word [bp+0x4],0x0
L_8981: jnz short L_899c
L_8983: sub_load ax,ax
L_8985: push ax
L_8986: push word [bp-0x8]
L_8989: call program_access
L_898c: add sp,0x4
L_898f: or_load ax,ax
L_8991: jnz short L_8998
L_8993: mov ax,0x1
L_8996: jmp short L_89f5
L_8998: sub_load ax,ax
L_899a: jmp short L_89f5
L_899c: mov word [bp-0x6],program_switch_c
L_89a1: mov ax,[bp+0x4]
L_89a4: mov [bp-0x4],ax
L_89a7: mov word [bp-0x2],0x0
L_89ac: cmp word [bp-0x8],0x0
L_89b0: jz short L_89e0
L_89b2: push word [program_environ]
L_89b6: lea ax,[bp-0x8]
L_89b9: push ax
L_89ba: push word [bp-0x8]
L_89bd: sub_load cx,cx
L_89bf: push cx
L_89c0: call program_spawnv
L_89c3: add sp,0x8
L_89c6: mov [bp-0xa],ax
L_89c9: inc ax
L_89ca: jnz short L_89da
L_89cc: cmp word [program_errno],0x2
L_89d1: jz short L_89e0
L_89d3: cmp word [program_errno],0xd
L_89d8: jz short L_89e0
L_89da: mov ax,[bp-0xa]
L_89dd: jmp short L_89f5
L_89df: nop
L_89e0: push word [program_environ]
L_89e4: lea ax,[bp-0x8]
L_89e7: push ax
L_89e8: mov cx,program_default_shell
L_89eb: mov [bp-0x8],cx
L_89ee: push cx
L_89ef: sub_load ax,ax
L_89f1: push ax
L_89f2: call program_spawn_search
L_89f5: mov_load sp,bp
L_89f7: pop bp
L_89f8: ret
