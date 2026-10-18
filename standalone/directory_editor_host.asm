; Diagnostic writes only its own proof; editor has no DOS/file IO.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern terminal_directory_edit
global _small_code_
_small_code_:
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
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0x1e41
 mov cx,2000
 rep stosw
 mov ah,2
 xor bh,bh
 mov dx,0x0711
 int 0x10
 mov ah,3
 int 0x10
 mov [old_shape],cx
 mov ax,editor_record
 push ax
 call terminal_directory_edit
 add sp,2
 mov [proof],ax
 mov ah,3
 xor bh,bh
 int 0x10
 cmp cx,[old_shape]
 jne .write
 cmp dx,0x0711
 jne .write
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,2000
.screen:
 cmp word [es:di],0x1e41
 jne .write
 add di,2
 loop .screen
 cmp word [text_video_segment],0xb800
 jne .write
 mov word [proof+2],1
.write:
 mov dx,proof_name
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc .failed
 mov bx,ax
 mov dx,proof
 mov cx,4
 mov ah,0x40
 int 0x21
 mov dx,editor_record
 mov cx,114
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
global text_video_segment,text_cga_status_port,editor_record
text_video_segment: dw 0xb800
text_cga_status_port: dw 0
old_shape: dw 0
proof: times 2 dw 0
proof_name: db 'RESULT.BIN',0
editor_record:
 db 'Original',0
 times 16 db 0x5a
 db 'bbs.local:23',0
 times 8 db 0x51
 dw 5
 db 0,8,1,0
 db 'SCRIPT',0,0x52,0x52
 db '01/02/26',0
 dw 42
 db 0,4,0
 db 'Secret123',0,0x54
 db 'KEY',0
 times 5 db 0x55
 db 'META',0
 times 4 db 0x56
 db 2
 db 'NOTE',0
 times 4 db 0x57
SEGMENT STACK stack align=16 class=STACK use16
 resb 4096
stack_top:
