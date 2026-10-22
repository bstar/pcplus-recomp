; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_collapse
extern window_offset16
extern window_restore_cell
extern window_collapse_delay
extern window_read_byte
extern window_frame
extern window_release
extern window_state_7a94
extern window_state_8fda
extern window_state_8fdc
extern window_state_8fde
extern window_state_7ac4
extern window_state_7a8e
extern window_state_7a66
extern window_state_7a72
extern window_state_7a74
extern window_state_7a7a
extern window_state_7ab2
%define short
%else
ORG 29486
%define window_offset16 31168
%define window_restore_cell 29939
%define window_collapse_delay 29952
%define window_read_byte 28576
%define window_frame 28652
%define window_release 30040
%define window_state_7a94 31380
%define window_state_8fda 36826
%define window_state_8fdc 36828
%define window_state_8fde 36830
%define window_state_7ac4 31428
%define window_state_7a8e 31374
%define window_state_7a66 31334
%define window_state_7a72 31346
%define window_state_7a74 31348
%define window_state_7a7a 31354
%define window_state_7ab2 31410
%endif
%include "encodings.inc"
window_collapse:
L_732e: push bp
L_732f: mov_load bp,sp
L_7331: sub sp,0xe
L_7334: push di
L_7335: push si
L_7336: cmp word [window_state_7a94],0x0
L_733b: jnz short L_7340
L_733d: jmp near L_74e2
L_7340: mov ax,[bp+0xa]
L_7343: sub ax,[bp+0xe]
L_7346: inc ax
L_7347: mov [bp-0x8],ax
L_734a: mov ax,[bp+0x8]
L_734d: sub ax,[bp+0xc]
L_7350: inc ax
L_7351: mov [bp-0xe],ax
L_7354: mov [bp-0x6],ax
L_7357: mov ah,[bp+0xe]
L_735a: sub_load al,al
L_735c: add ax,[bp+0xc]
L_735f: add ax,0x101
L_7362: mov [bp-0xc],ax
L_7365: mov ax,[bp+0x4]
L_7368: mov dx,[bp+0x6]
L_736b: mov [window_state_8fda],ax
L_736e: mov [window_state_8fdc],dx
L_7372: mov word [window_state_8fde],0x8
L_7378: cmp word [window_state_7ac4],0x64
L_737d: jl short L_738d
L_737f: cmp word [window_state_7a8e],0x0
L_7384: jnz short L_738d
L_7386: cmp word [window_state_7a66],0x0
L_738b: jz short L_7393
L_738d: mov word [window_state_8fde],0x1
L_7393: mov dx,[bp-0x6]
L_7396: cmp dx,[bp-0x8]
L_7399: jna short L_739e
L_739b: mov dx,[bp-0x8]
L_739e: mov [bp-0x2],dx
L_73a1: cmp dx,0x3
L_73a4: jnc short L_73ab
L_73a6: mov word [bp-0x2],0x3
L_73ab: mov ax,[bp-0x2]
L_73ae: mov cx,0x3
L_73b1: sub_load dx,dx
L_73b3: div cx
L_73b5: mov_load cx,ax
L_73b7: mov ax,0x8
L_73ba: sub_load dx,dx
L_73bc: div cx
L_73be: add [window_state_8fde],ax
L_73c2: mov ax,[window_state_7a72]
L_73c5: sub ax,strict word 0x3
L_73c8: cmp ax,[bp+0x8]
L_73cb: jng short L_7426
L_73cd: mov ax,[window_state_7a74]
L_73d0: dec ax
L_73d1: dec ax
L_73d2: cmp ax,[bp+0xa]
L_73d5: jng short L_7426
L_73d7: mov ah,[bp+0xe]
L_73da: inc ah
L_73dc: sub_load al,al
L_73de: mov cx,[bp+0x8]
L_73e1: inc cx
L_73e2: or_load ax,cx
L_73e4: push ax
L_73e5: call window_offset16
L_73e8: mov_load si,ax
L_73ea: mov ax,[bp+0xa]
L_73ed: sub ax,[bp+0xe]
L_73f0: mov [bp-0x2],ax
L_73f3: jmp short L_7404
L_73f5: mov_load ax,si
L_73f7: call window_restore_cell
L_73fa: lea ax,[si+0x2]
L_73fd: call window_restore_cell
L_7400: add si,[window_state_7a7a]
L_7404: mov ax,[bp-0x2]
L_7407: dec word [bp-0x2]
L_740a: or_load ax,ax
L_740c: jnz short L_73f5
L_740e: inc si
L_740f: inc si
L_7410: mov di,[bp-0xe]
L_7413: jmp short L_741c
L_7415: mov_load ax,si
L_7417: call window_restore_cell
L_741a: dec si
L_741b: dec si
L_741c: mov_load ax,di
L_741e: dec di
L_741f: or_load ax,ax
L_7421: jnz short L_7415
L_7423: call window_collapse_delay
L_7426: mov ah,[bp+0xe]
L_7429: sub_load al,al
L_742b: or ax,[bp+0xc]
L_742e: push ax
L_742f: call window_offset16
L_7432: mov_load si,ax
L_7434: lea ax,[si+0x1]
L_7437: push ax
L_7438: call window_read_byte
L_743b: mov [bp-0xa],ax
L_743e: mov di,[bp-0x6]
L_7441: jmp short L_7445
L_7443: inc si
L_7444: inc si
L_7445: mov_load ax,si
L_7447: call window_restore_cell
L_744a: dec di
L_744b: jnz short L_7443
L_744d: add si,[window_state_7a7a]
L_7451: dec word [bp-0x8]
L_7454: jnz short L_7459
L_7456: jmp near L_74e2
L_7459: mov di,[bp-0x8]
L_745c: jmp short L_7462
L_745e: add si,[window_state_7a7a]
L_7462: mov_load ax,si
L_7464: call window_restore_cell
L_7467: dec di
L_7468: jnz short L_745e
L_746a: dec si
L_746b: dec si
L_746c: dec word [bp-0x6]
L_746f: jz short L_74e2
L_7471: mov ax,[bp-0x6]
L_7474: mov [bp-0x2],ax
L_7477: jmp short L_747b
L_7479: dec si
L_747a: dec si
L_747b: mov_load ax,si
L_747d: call window_restore_cell
L_7480: dec word [bp-0x2]
L_7483: jnz short L_7479
L_7485: sub si,[window_state_7a7a]
L_7489: dec word [bp-0x8]
L_748c: jz short L_74e2
L_748e: mov di,[bp-0x8]
L_7491: jmp short L_7497
L_7493: sub si,[window_state_7a7a]
L_7497: mov_load ax,si
L_7499: call window_restore_cell
L_749c: dec di
L_749d: jnz short L_7493
L_749f: mov [bp-0x4],si
L_74a2: add word [bp-0x4],0x2
L_74a6: dec word [bp-0x6]
L_74a9: jz short L_74e2
L_74ab: mov dh,[bp-0x8]
L_74ae: sub_load dl,dl
L_74b0: add dx,[bp-0xc]
L_74b3: add dx,[bp-0x6]
L_74b6: sub dx,0x101
L_74ba: cmp word [bp-0x8],0x1
L_74be: jna short L_74d4
L_74c0: cmp word [bp-0x6],0x1
L_74c4: jna short L_74d4
L_74c6: push word [bp-0xc]
L_74c9: push dx
L_74ca: push word [bp-0xa]
L_74cd: push word [window_state_7ab2]
L_74d1: call window_frame
L_74d4: call window_collapse_delay
L_74d7: add word [bp-0xc],0x101
L_74dc: mov si,[bp-0x4]
L_74df: jmp near L_743e
L_74e2: push word [bp+0x6]
L_74e5: push word [bp+0x4]
L_74e8: call window_release
L_74eb: pop si
L_74ec: pop di
L_74ed: mov_load sp,bp
L_74ef: pop bp
L_74f0: ret word 0xc
