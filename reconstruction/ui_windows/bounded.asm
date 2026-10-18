; Maintained geometry/capacity wrapper, NOT recovered original instructions.
; Near stack ABI: top,left,height,width,buffer,capacity_bytes; RET 12.
; AX=0 success,1 invalid. Preserves BP/SI/DI/BX; DF must be clear, DS=SS.
; Caller owns buffer allocation/nonoverlap and cursor/terminal logical state.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global ui_window_save,ui_window_restore
extern pcplus_screen_save,pcplus_screen_restore
extern screen_columns,ui_window_rows
ui_window_save:
 xor ax,ax
 jmp window_transfer
ui_window_restore:
 mov ax,1
window_transfer:
 push bp
 mov bp,sp
 push si
 push di
 push bx
 sub sp,6
 mov [bp-8],ax
 mov ax,[screen_columns]
 or ax,ax
 jz .bad
 cmp ax,255
 ja .bad
 mov ax,[ui_window_rows]
 or ax,ax
 jz .bad
 cmp ax,127
 ja .bad
 mov ax,[bp+8]
 or ax,ax
 jz .bad
 add ax,[bp+4]
 jc .bad
 cmp ax,[ui_window_rows]
 ja .bad
 mov ax,[bp+10]
 or ax,ax
 jz .bad
 add ax,[bp+6]
 jc .bad
 cmp ax,[screen_columns]
 ja .bad
 mov ax,[bp+8]
 mul word [bp+10]
 or dx,dx
 jnz .bad
 shl ax,1
 jc .bad
 cmp ax,[bp+14]
 ja .bad
 add ax,[bp+12]
 jc .bad
 mov ax,[bp+4]
 mul word [screen_columns]
 add ax,[bp+6]
 shl ax,1
 mov di,ax
 mov si,[bp+12]
 mov ax,[bp+8]
 mov [bp-12],ax
.row:
 push si
 push di
 push word [bp+10]
 cmp word [bp-8],0
 jne .restore
 call pcplus_screen_save
 jmp .advance
.restore:
 call pcplus_screen_restore
.advance:
 mov ax,[bp+10]
 shl ax,1
 add si,ax
 mov ax,[screen_columns]
 shl ax,1
 add di,ax
 dec word [bp-12]
 jnz .row
 xor ax,ax
 jmp .done
.bad:
 mov ax,1
.done:
 lea sp,[bp-6]
 pop bx
 pop di
 pop si
 pop bp
 ret 12
