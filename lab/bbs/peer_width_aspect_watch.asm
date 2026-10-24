; Read-only observer for actual BBS/ASPECT width composition.
; Identify root DS at a BIOS cursor operation after the first real wide request.
bits 16
cpu 8086
org 100h
%include "bbs_width_offsets.inc"
jmp start
old10: dw 0,0
old21: dw 0,0
old1c: dw 0,0
sample:
 dw 0x4257,1
root_ds: dw 0
root_ss: dw 0
child_count: dw 0
child_status: dw 0xffff
child_ds: dw 0
child_ss: dw 0
root_status: dw 0xffff
attached_ticks: dw 0
bridge_ticks: dw 0
overlay_ticks: dw 0
final_width: dw 0
final_parser: dw 0xffff
final_scope: dw 0xffff
final_wait: dw 0xffff
final_live: dw 0xffff
final_bank: dw 0xffff
final_program: dw 0xffff
final_aspect: dw 0xffff
staged: dw 0
sample_end:
filename: db 'D:\BBSOBS.BIN',0
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
 jne .done
 cmp word [SCREEN_COLUMNS],80
 jne .done
 cmp word [SCREEN_ATTRIBUTE_ROW_BYTES],132
 jne .done
 cmp word [SCREEN_ATTRIBUTES_BASE],SCREEN_ATTRIBUTE_CELLS
 jne .done
 cmp word [TERMINAL_ASPECT_ACTIVE],1
 jne .done
 mov [cs:root_ds],ds
 mov [cs:root_ss],ss
 mov word [cs:staged],1
.done:
 restore
 jmp far [cs:old10]
handler1c:
 save
 cmp word [cs:staged],1
 jne .done
 cmp word [cs:root_status],0xffff
 jne .done
 mov ax,[cs:root_ds]
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 cmp word [es:RENDER_ATTACHED],1
 jne .done
 inc word [cs:attached_ticks]
 cmp word [es:RESIDENT_BRIDGE_BUSY],1
 jne .overlay
 inc word [cs:bridge_ticks]
.overlay:
 cmp word [es:TERMINAL_SCRIPT_OVERLAY_VISIBLE],1
 jne .done
 inc word [cs:overlay_ticks]
.done:
 restore
 jmp far [cs:old1c]
handler21:
 pushf
 cmp ah,0x4c
 jne .skip
 popf
 save
 cmp word [cs:staged],1
 jne .done
 cmp word [cs:root_status],0xffff
 jne .done
 xor ah,ah
 mov bx,ds
 cmp bx,[cs:root_ds]
 je .root
 inc word [cs:child_count]
 mov [cs:child_status],ax
 mov [cs:child_ds],ds
 mov [cs:child_ss],ss
 jmp .done
.root:
 mov [cs:root_status],ax
 mov ax,[SCREEN_ATTRIBUTE_ROW_BYTES]
 mov [cs:final_width],ax
 mov ax,[TERMINAL_PARSER_ACTIVE]
 mov [cs:final_parser],ax
 mov ax,[TERMINAL_ASPECT_ACTIVE]
 mov [cs:final_scope],ax
 mov ax,[TERMINAL_ANSI_WAIT_ACTIVE]
 mov [cs:final_wait],ax
 mov ax,[PROGRAM_ACTIVE]
 mov [cs:final_program],ax
 mov ax,ds
 sub ax,DGROUP_REL
 add ax,LIVE_CODE_REL
 mov es,ax
 mov ax,[es:RESET_LIVE_ACTIVE]
 mov [cs:final_live],ax
 mov ax,[es:RESET_BANK_BUSY]
 mov [cs:final_bank],ax
 mov ax,ds
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 mov ax,[es:RENDER_ATTACHED]
 mov [cs:final_aspect],ax
 push cs
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .done
 mov bx,ax
 mov dx,sample
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
 ; Remove every observer hook before the independent after-snapshot.
 ; Restore21 last so DOS vector updates still use the normal chained entry.
 mov dx,[cs:old10]
 mov ds,[cs:old10+2]
 mov ax,0x2510
 int 0x21
 mov dx,[cs:old1c]
 mov ds,[cs:old1c+2]
 mov ax,0x251c
 int 0x21
 mov dx,[cs:old21]
 mov ds,[cs:old21+2]
 mov ax,0x2521
 int 0x21
.done:
 restore
 jmp .chain
.skip:
 popf
.chain:
 jmp far [cs:old21]
start:
 mov ax,0x3510
 int 0x21
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [old21+2],es
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,handler10
 mov ax,0x2510
 int 0x21
 mov dx,handler21
 mov ax,0x2521
 int 0x21
 mov dx,handler1c
 mov ax,0x251c
 int 0x21
 mov dx,(start-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
