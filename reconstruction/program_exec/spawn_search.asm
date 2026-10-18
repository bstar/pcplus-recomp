; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_spawn_search
extern program_getenv
extern program_spawnv
extern program_strcat
extern program_strlen
extern program_strchr
extern program_path_component
extern program_service_92a8
extern program_service_92a4
extern program_errno
extern program_path_name
extern program_heap_mode
extern program_state_7dc9
%define short
%else
ORG 0xa4a6
%define program_getenv 0x8e12
%define program_spawnv 0x68ee
%define program_strcat 0x8bea
%define program_strlen 0x8d18
%define program_strchr 0x8c2a
%define program_path_component 0xa8e6
%define program_service_92a8 0x92a8
%define program_service_92a4 0x92a4
%define program_errno 0x7b1c
%define program_path_name 0x7dc4
%define program_heap_mode 0x7b54
%define program_state_7dc9 0x7dc9
%endif
%include "encodings.inc"
program_spawn_search:
L_a4a6: push bp
L_a4a7: mov_load bp,sp
L_a4a9: sub sp,0x8
L_a4ac: push di
L_a4ad: push si
L_a4ae: sub_load di,di
L_a4b0: mov ax,[program_heap_mode]
L_a4b3: mov [bp-0x2],ax
L_a4b6: mov word [program_heap_mode],0x10
L_a4bc: push word [bp+0xa]
L_a4bf: push word [bp+0x8]
L_a4c2: push word [bp+0x6]
L_a4c5: push word [bp+0x4]
L_a4c8: call program_spawnv
L_a4cb: add sp,0x8
L_a4ce: mov [bp-0x4],ax
L_a4d1: inc ax
L_a4d2: jnz short L_a52b
L_a4d4: cmp word [program_errno],0x2
L_a4d9: jnz short L_a52b
L_a4db: mov ax,0x2f
L_a4de: push ax
L_a4df: push word [bp+0x6]
L_a4e2: call program_strchr
L_a4e5: add sp,0x4
L_a4e8: or_load ax,ax
L_a4ea: jnz short L_a52b
L_a4ec: mov ax,0x5c
L_a4ef: push ax
L_a4f0: push word [bp+0x6]
L_a4f3: call program_strchr
L_a4f6: add sp,0x4
L_a4f9: or_load ax,ax
L_a4fb: jnz short L_a52b
L_a4fd: mov bx,[bp+0x6]
L_a500: cmp byte [bx],0x0
L_a503: jz short L_a50b
L_a505: cmp byte [bx+0x1],0x3a
L_a509: jz short L_a52b
L_a50b: mov ax,program_path_name
L_a50e: push ax
L_a50f: call program_getenv
L_a512: add sp,0x2
L_a515: mov_load si,ax
L_a517: or_load si,si
L_a519: jz short L_a52b
L_a51b: mov ax,0x104
L_a51e: push ax
L_a51f: call program_service_92a8
L_a522: add sp,0x2
L_a525: mov_load di,ax
L_a527: or_load di,di
L_a529: jnz short L_a534
L_a52b: mov ax,[bp-0x2]
L_a52e: mov [program_heap_mode],ax
L_a531: jmp near L_a5d4
L_a534: mov ax,[bp-0x2]
L_a537: mov [program_heap_mode],ax
L_a53a: jmp near L_a5bf
L_a53d: nop
L_a53e: cmp byte [di],0x0
L_a541: jnz short L_a546
L_a543: jmp near L_a5d4
L_a546: push di
L_a547: call program_strlen
L_a54a: add sp,0x2
L_a54d: mov_load bx,ax
L_a54f: add_load bx,di
L_a551: dec bx
L_a552: cmp byte [bx],0x5c
L_a555: jz short L_a567
L_a557: cmp byte [bx],0x2f
L_a55a: jz short L_a567
L_a55c: mov ax,program_state_7dc9
L_a55f: push ax
L_a560: push di
L_a561: call program_strcat
L_a564: add sp,0x4
L_a567: push word [bp+0x6]
L_a56a: call program_strlen
L_a56d: add sp,0x2
L_a570: push di
L_a571: mov [bp-0x8],ax
L_a574: call program_strlen
L_a577: add sp,0x2
L_a57a: add ax,[bp-0x8]
L_a57d: cmp ax,0x104
L_a580: jnc short L_a5d4
L_a582: push word [bp+0x6]
L_a585: push di
L_a586: call program_strcat
L_a589: add sp,0x4
L_a58c: push word [bp+0xa]
L_a58f: push word [bp+0x8]
L_a592: push di
L_a593: push word [bp+0x4]
L_a596: call program_spawnv
L_a599: add sp,0x8
L_a59c: mov [bp-0x4],ax
L_a59f: inc ax
L_a5a0: jnz short L_a5d4
L_a5a2: cmp word [program_errno],0x2
L_a5a7: jz short L_a5bf
L_a5a9: cmp byte [di],0x5c
L_a5ac: jz short L_a5b3
L_a5ae: cmp byte [di],0x2f
L_a5b1: jnz short L_a5d4
L_a5b3: cmp byte [di+0x1],0x5c
L_a5b7: jz short L_a5bf
L_a5b9: cmp byte [di+0x1],0x2f
L_a5bd: jnz short L_a5d4
L_a5bf: mov ax,0x103
L_a5c2: push ax
L_a5c3: push di
L_a5c4: push si
L_a5c5: call program_path_component
L_a5c8: add sp,0x6
L_a5cb: mov_load si,ax
L_a5cd: or_load si,si
L_a5cf: jz short L_a5d4
L_a5d1: jmp near L_a53e
L_a5d4: or_load di,di
L_a5d6: jz short L_a5df
L_a5d8: push di
L_a5d9: call program_service_92a4
L_a5dc: add sp,0x2
L_a5df: mov ax,[bp-0x4]
L_a5e2: pop si
L_a5e3: pop di
L_a5e4: mov_load sp,bp
L_a5e6: pop bp
L_a5e7: ret
