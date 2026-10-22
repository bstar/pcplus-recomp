; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_frame
extern window_cell
extern window_horizontal
extern window_vertical
%define short
%else
ORG 28652
%define window_cell 32610
%define window_horizontal 31144
%define window_vertical 32586
%endif
%include "encodings.inc"
window_frame:
L_6fec: push bp
L_6fed: mov_load bp,sp
L_6fef: push di
L_6ff0: push si
L_6ff1: mov di,[bp+0xa]
L_6ff4: mov si,[bp+0x4]
L_6ff7: mov ax,[bp+0x6]
L_6ffa: mov ah,[si]
L_6ffc: push ax
L_6ffd: push di
L_6ffe: call window_cell
L_7001: mov_load dx,di
L_7003: mov bx,[bp+0x8]
L_7006: mov_load dl,bl
L_7008: push dx
L_7009: mov ax,[bp+0x6]
L_700c: mov ah,[si+0x2]
L_700f: push ax
L_7010: push dx
L_7011: call window_cell
L_7014: mov ax,[bp+0x6]
L_7017: mov ah,[si+0x4]
L_701a: push ax
L_701b: push word [bp+0x8]
L_701e: call window_cell
L_7021: mov ax,[bp+0x6]
L_7024: mov ah,[si+0x6]
L_7027: push ax
L_7028: mov_load ax,di
L_702a: mov bx,[bp+0x8]
L_702d: mov_load ah,bh
L_702f: push ax
L_7030: call window_cell
L_7033: mov ax,[bp+0x6]
L_7036: mov ah,[si+0x5]
L_7039: mov_load bx,di
L_703b: inc bx
L_703c: mov cx,[bp+0x8]
L_703f: mov_load dx,di
L_7041: xor_load ch,ch
L_7043: sub_load cl,dl
L_7045: dec cx
L_7046: push ax
L_7047: mov dx,[bp+0x8]
L_704a: mov_load dl,bl
L_704c: push dx
L_704d: push cx
L_704e: mov ah,[si+0x1]
L_7051: push ax
L_7052: push bx
L_7053: push cx
L_7054: call window_horizontal
L_7057: call window_horizontal
L_705a: mov ax,[bp+0x6]
L_705d: mov ah,[si+0x3]
L_7060: mov_load bx,di
L_7062: inc bh
L_7064: mov cx,[bp+0x8]
L_7067: mov_load dx,di
L_7069: sub_load ch,dh
L_706b: mov_load cl,ch
L_706d: xor_load ch,ch
L_706f: dec cx
L_7070: pop dx
L_7071: inc dh
L_7073: push ax
L_7074: push dx
L_7075: push cx
L_7076: mov ah,[si+0x7]
L_7079: push ax
L_707a: push bx
L_707b: push cx
L_707c: call window_vertical
L_707f: call window_vertical
L_7082: pop si
L_7083: pop di
L_7084: pop bp
L_7085: ret word 0x8
