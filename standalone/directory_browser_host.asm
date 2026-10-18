; Standalone actual DOS browser diagnostic; proof output belongs to test only.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern terminal_directory_choose
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
 cmp byte [es:0x82],'L'
 jne .mode
 mov word [terminal_directory_codes],1
.mode:
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
 call terminal_directory_choose
 mov [proof],ax
 mov ax,[terminal_directory_entry]
 mov [proof+2],ax
 mov ax,[terminal_directory_codes]
 mov [proof+8],ax
 mov ah,3
 xor bh,bh
 int 0x10
 mov [proof+4],dx
 cmp cx,[old_shape]
 jne .bad
 cmp dx,0x0711
 jne .bad
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,2000
.screen:
 cmp word [es:di],0x1e41
 jne .bad
 add di,2
 loop .screen
 cmp word [text_video_segment],0xb800
 jne .bad
 mov word [proof+6],1
.bad:
 mov dx,proof_name
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc .failed
 mov bx,ax
 mov dx,proof
 mov cx,10
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
global terminal_directory_path,terminal_directory_entry,terminal_directory_codes,text_video_segment,text_cga_status_port
terminal_directory_path: db 'NORMAL.DIR',0
 times 53 db 0
terminal_directory_entry: dw 0
terminal_directory_codes: dw 0
text_video_segment: dw 0xb800
text_cga_status_port: dw 0
old_shape: dw 0
proof: times 5 dw 0
proof_name: db 'RESULT.BIN',0
SEGMENT _BSS public align=16 class=BSS use16
 resb 2
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
stack_top:
