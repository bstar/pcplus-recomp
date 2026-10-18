; Maintained far screen-buffer API, retaining recovered packed-cell services.
; AX=count<=2000, DX=video offset; save ES:DI / restore ES:SI.
; All registers preserved; DS=SS required at entry and retained on return.
; Native packed-cell reads retain their temporary video-DS window.
; CF1 invalid extent, CF0 success.
; Caller supplies allocated nonoverlapping buffer; DF=0 is the shared UI ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern ui_read_packed,text_write_packed
global terminal_screen_save_far,terminal_screen_restore_far
%macro save_regs 0
 push bp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro return_regs 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 ret
%endmacro
terminal_screen_save_far:
 save_regs
 cmp ax,2000
 ja .invalid
 or ax,ax
 jz .done
 mov bx,ax
 shl bx,1
 neg bx ;Largest legal offset, including a view ending exactly at64KiB.
 cmp dx,bx
 ja .invalid
 cmp di,bx
 ja .invalid
 mov bp,ax
 mov si,dx
 cld
.copy:
 push si
 add si,2
 call ui_read_packed
 stosw
 dec bp
 jnz .copy
.done:
 clc
 return_regs
.invalid:
 stc
 return_regs

terminal_screen_restore_far:
 save_regs
 cmp ax,2000
 ja .invalid
 or ax,ax
 jz .done
 mov bx,ax
 shl bx,1
 neg bx
 cmp dx,bx
 ja .invalid
 cmp si,bx
 ja .invalid
 mov bp,ax
 mov di,dx
 cld
.copy:
 mov ax,[es:si]
 add si,2
 push es
 push ax
 push di
 add di,2
 call text_write_packed
 pop es
 dec bp
 jnz .copy
.done:
 clc
 return_regs
.invalid:
 stc
 return_regs
