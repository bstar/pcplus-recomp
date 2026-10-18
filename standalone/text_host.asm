; Actual video-memory assertions for the independently linked output backend.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern text_put_cell,text_put_char,text_put_packed,text_fill,text_put_bios
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,3
 int 0x10
 xor ax,ax
 mov dx,0x1e
 mov cx,'A'
 call text_put_cell
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x1e41
 jne .failed
 xor ax,ax
 mov cx,'B'
 call text_put_char
 cmp word [es:0],0x1e42
 jne .failed
 mov ax,2
 mov cx,0x432a
 call text_put_packed
 cmp word [es:2],0x2a43
 jne .failed
 mov ax,4
 mov dx,3
 mov cx,0x443b
 call text_fill
 cmp word [es:4],0x3b44
 jne .failed
 cmp word [es:8],0x3b44
 jne .failed
 ; Use the recovered BIOS branch at the current cursor (0,0).
 mov word [text_bios_output],1
 xor ax,ax
 mov dx,0x4f
 mov cx,'Z'
 call text_put_cell
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x4f5a
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
global text_video_segment,text_bios_output,text_cga_status_port
text_video_segment: dw 0xb800
text_bios_output: dw 0
text_cga_status_port: dw 0
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
