; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_invoke
extern meta_keys_send_text
extern meta_keys_hook
extern meta_keys_message
extern meta_keys_aspect_service
extern meta_keys_program_service
extern meta_script_active
extern meta_script_busy_message
%define short
%else
ORG 0x47b6
%define meta_keys_send_text 0x48cc
%define meta_keys_hook 0x414c
%define meta_keys_message 0x427f
%define meta_keys_aspect_service 0x4b1f
%define meta_keys_program_service 0x433d
%define meta_script_active 0x4b02
%define meta_script_busy_message 0x4430
%endif
%include "encodings.inc"
meta_keys_invoke:
L_47b6: push bp
L_47b7: mov_load bp,sp
L_47b9: mov ax,[bp+0x6]
L_47bc: or_load ax,ax
L_47be: jz short L_47cb
L_47c0: dec ax
L_47c1: jz short L_47e6
L_47c3: dec ax
L_47c4: jz short L_47f9
L_47c6: dec ax
L_47c7: jz short L_480b
L_47c9: jmp short L_4812
L_47cb: cmp word [meta_script_active],0x0
L_47d0: jz short L_47db
L_47d2: lea bx,[meta_script_busy_message]
L_47d6: call meta_keys_message
L_47d9: jmp short L_4812
L_47db: push word [bp+0x4]
L_47de: sub_load ax,ax
L_47e0: push ax
L_47e1: call meta_keys_aspect_service
L_47e4: jmp short L_4812
L_47e6: mov ax,0x1
L_47e9: push ax
L_47ea: push ax
L_47eb: push ax
L_47ec: sub_load ax,ax
L_47ee: push ax
L_47ef: push word [bp+0x4]
L_47f2: call meta_keys_program_service
L_47f5: mov_load sp,bp
L_47f7: jmp short L_4812
L_47f9: push word [bp+0x4]
L_47fc: push word [bp+0x8]
L_47ff: sub_load ax,ax
L_4801: push ax
L_4802: mov ax,0x1
L_4805: push ax
L_4806: call meta_keys_hook
L_4809: jmp short L_4812
L_480b: push word [bp+0x4]
L_480e: call meta_keys_send_text
L_4811: pop bx
L_4812: mov_load sp,bp
L_4814: pop bp
L_4815: ret
