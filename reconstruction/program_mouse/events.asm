; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _TEXT public class=CODE use16
global mouse_events
extern mouse_absolute
extern mouse_flags
extern mouse_enabled
extern mouse_code
extern mouse_button_pending
extern mouse_count
extern mouse_motion_y
extern mouse_base_y
extern mouse_scale_y
extern mouse_motion_x
extern mouse_base_x
extern mouse_scale_x
%define short
%else
ORG 32922
%define mouse_absolute 40294
%define mouse_flags 31318
%define mouse_enabled 24046
%define mouse_code 31332
%define mouse_button_pending 31328
%define mouse_count 31330
%define mouse_motion_y 31322
%define mouse_base_y 31326
%define mouse_scale_y 31314
%define mouse_motion_x 31320
%define mouse_base_x 31324
%define mouse_scale_x 31312
%endif
%include "encodings.inc"
mouse_events:
L_809a: push bp
L_809b: mov_load bp,sp
L_809d: sub sp,0x6
L_80a0: push di
L_80a1: test byte [mouse_flags],0xa
L_80a6: jz short L_80d3
L_80a8: mov al,[mouse_flags]
L_80ab: and ax,strict word 0x2
L_80ae: cmp ax,strict word 0x1
L_80b1: sbb_load bx,bx
L_80b3: and bx,0x1
L_80b6: add bx,0x4
L_80b9: cmp byte [bx+mouse_enabled],0x0
L_80be: jnz short L_80c3
L_80c0: jmp near L_8157
L_80c3: mov [mouse_code],bx
L_80c7: mov ax,0x1
L_80ca: mov [mouse_button_pending],ax
L_80cd: mov [mouse_count],ax
L_80d0: jmp near L_8157
L_80d3: cmp word [mouse_count],0x0
L_80d8: jnz short L_8157
L_80da: mov ax,[mouse_motion_y]
L_80dd: sub ax,[mouse_base_y]
L_80e1: cwd
L_80e2: idiv word [mouse_scale_y]
L_80e6: mov [bp-0x4],ax
L_80e9: mov ax,[mouse_motion_x]
L_80ec: sub ax,[mouse_base_x]
L_80f0: cwd
L_80f1: idiv word [mouse_scale_x]
L_80f5: mov [bp-0x2],ax
L_80f8: or_load ax,ax
L_80fa: jnz short L_8101
L_80fc: cmp [bp-0x4],ax
L_80ff: jz short L_8157
L_8101: mov ax,[mouse_motion_x]
L_8104: mov [mouse_base_x],ax
L_8107: mov ax,[mouse_motion_y]
L_810a: mov [mouse_base_y],ax
L_810d: push word [bp-0x2]
L_8110: call mouse_absolute
L_8113: pop bx
L_8114: mov_load di,ax
L_8116: push word [bp-0x4]
L_8119: call mouse_absolute
L_811c: pop bx
L_811d: cmp_load ax,di
L_811f: ja short L_813c
L_8121: cmp word [bp-0x2],0x0
L_8125: jng short L_812c
L_8127: mov bx,0x1
L_812a: jmp short L_812f
L_812c: mov bx,0x3
L_812f: cmp byte [bx+mouse_enabled],0x0
L_8134: jz short L_8157
L_8136: mov [mouse_count],di
L_813a: jmp short L_8153
L_813c: cmp word [bp-0x4],0x0
L_8140: jng short L_8147
L_8142: mov bx,0x2
L_8145: jmp short L_8149
L_8147: sub_load bx,bx
L_8149: cmp byte [bx+mouse_enabled],0x0
L_814e: jz short L_8157
L_8150: mov [mouse_count],ax
L_8153: mov [mouse_code],bx
L_8157: pop di
L_8158: mov_load sp,bp
L_815a: pop bp
L_815b: ret
