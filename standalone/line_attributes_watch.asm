; Test-only BIOS-boundary state fixture and passive DOS-exit observer.
; No product code is patched. The declared cursor position stages bounded
; plane data once; all subsequent parsing, editing and video uses the product.
BITS 16
CPU 8086
ORG 100h
%include "line_attributes_offsets.inc"
jmp start
old10: dw 0,0
old21: dw 0,0
sample:
 dw 0x4c41
staged: dw 0
exits: dw 0
exit_status: dw 0xffff
parent_ds: dw 0
parent_ss: dw 0
wrap: dw 0
normal: dw 0
cell_count: dw 0
row: dw 0
column: dw 0
frames: dw 0
flags: times 4096 db 0
values: times 4096 db 0
video: times 4000 db 0
sample_end:
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cld
%endmacro
%macro restore 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
%endmacro
handler10:
 save
 cmp ah,2
 jne .done
 cmp word [cs:staged],0
 jne .observe
 cmp dx,0x0511
 jne .done
 cmp word [SCREEN_COLUMNS],80
 jne .done
 cmp word [SCREEN_ATTRIBUTES_BASE],SCREEN_ATTRIBUTE_CELLS
 jne .done
 cmp word [ERASE_ATTRIBUTE_VALUES_BASE],ERASE_ATTRIBUTE_VALUES
 jne .done
 push ds
 pop es
 mov di,SCREEN_ATTRIBUTE_CELLS
 mov al,0x55
 mov cx,4096
 rep stosb
 mov di,SCREEN_ATTRIBUTE_CELLS
 xor ax,ax
 mov cx,2000
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,0x66
 mov cx,4096
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,7
 mov cx,2000
 rep stosb
 mov byte [SCREEN_ATTRIBUTE_CELLS+3*80+50],0x80
 mov byte [SCREEN_ATTRIBUTE_CELLS+10*80],0x81
 mov word [SCREEN_CURSOR_WRAP],1
 inc word [cs:staged]
 jmp .done
.observe:
 cmp dx,0x184f
 jne .done
 cmp word [SCREEN_COLUMNS],80
 jne .done
 cmp word [SCREEN_ATTRIBUTES_BASE],SCREEN_ATTRIBUTE_CELLS
 jne .done
 call snapshot
 inc word [cs:frames]
.done:
 restore
 jmp far [cs:old10]
handler21:
 save
 cmp ah,0x4c
 jne .done
 cmp word [cs:staged],1
 jne .done
 cmp word [cs:exits],0
 jne .done
 cmp word [SCREEN_COLUMNS],80
 jne .done
 cmp word [SCREEN_ATTRIBUTES_BASE],SCREEN_ATTRIBUTE_CELLS
 jne .done
 cmp word [ERASE_ATTRIBUTE_VALUES_BASE],ERASE_ATTRIBUTE_VALUES
 jne .done
 xor ah,ah
 mov [cs:exit_status],ax
 mov ax,ds
 mov [cs:parent_ds],ax
 mov ax,ss
 mov [cs:parent_ss],ax
 mov ax,[SCREEN_CURSOR_WRAP]
 mov [cs:wrap],ax
 mov ax,[ATTRIBUTES_NORMAL_VALUE]
 mov [cs:normal],ax
 mov ax,[ERASE_CELL_COUNT]
 mov [cs:cell_count],ax
 mov ax,[SCREEN_CURSOR_ROW]
 mov [cs:row],ax
 mov ax,[SCREEN_CURSOR_COLUMN]
 mov [cs:column],ax
 inc word [cs:exits]
.done:
 restore
 jmp far [cs:old21]
snapshot:
 push cs
 pop es
 mov si,SCREEN_ATTRIBUTE_CELLS
 mov di,flags
 mov cx,4096
 rep movsb
 mov si,ERASE_ATTRIBUTE_VALUES
 mov di,values
 mov cx,4096
 rep movsb
 push ds
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov di,video
 mov cx,2000
 rep movsw
 pop ds
 ret
resident_end:
start:
 cmp byte [0x82],'T'
 jne collect
 mov ax,0x3510
 int 0x21
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [old21+2],es
 mov dx,handler10
 mov ax,0x2510
 int 0x21
 mov dx,handler21
 mov ax,0x2521
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 mov ax,0x3521
 int 0x21
 cmp bx,handler21
 jne failed
 cmp word [es:sample],0x4c41
 jne failed
 mov ax,[es:old10]
 mov [old10],ax
 mov ax,[es:old10+2]
 mov [old10+2],ax
 mov ax,[es:old21]
 mov [old21],ax
 mov ax,[es:old21+2]
 mov [old21+2],ax
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,sample_end-sample
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[old21]
 mov ax,[old21+2]
 push ds
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 mov dx,[old10]
 mov ax,[old10+2]
 push ds
 mov ds,ax
 mov ax,0x2510
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,sample_end-sample
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\LINEATTR.BIN',0
buffer: times sample_end-sample db 0
