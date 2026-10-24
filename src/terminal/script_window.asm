; Cooperative production Alt-Z and retained native blocking-window component.
; The child retains UART/VM ownership. Only checked foreground RPC services
; borrow the inactive redisplay frame. No DOS IO, parser or parent UART IO.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern keyboard_poll,keyboard_read
global terminal_script_window_keyboard_poll,terminal_script_window_keyboard_read
terminal_script_window_keyboard_poll:
 call keyboard_poll
 retf
terminal_script_window_keyboard_read:
 call keyboard_read
 retf
SEGMENT ASPECT_CODE public class=FARCODE use16
extern aspect_local_window,terminal_script_window_poll
extern terminal_aspect_active,keyboard_debug_gate
extern redisplay_view,_redisplay_active,_command_menu_active
extern keyboard_mapping_hook_enabled,keyboard_mapping_hook_character
global terminal_script_window,terminal_script_window_debug
global local_window_save,local_window_draw,local_window_keyboard_select
global local_window_write,local_window_format,local_window_status_draw
global local_window_key_poll,local_window_key_read,local_window_restore
global terminal_script_window_active,terminal_script_window_error
global terminal_script_window_open,terminal_script_window_service
global terminal_script_window_hide,terminal_script_window_close
global terminal_script_overlay_visible
terminal_script_overlay_visible equ saved
global terminal_script_window_cooperative
global terminal_script_confirm,terminal_script_confirm_active

; Scalar confirmation owner:0 begin,1 No,2 Yes,3 retire,4 idle repaint.
; The child executes native yes/no and owns all key reads and live receive.
terminal_script_confirm:
 cmp bx,4
 ja .operand
 or bx,bx
 jz .begin
 cmp word [cs:terminal_script_window_cooperative],1
 jne .unowned
 cmp word [cs:page],2
 jne .unowned
 cmp bx,3
 je .retire
 cmp bx,4
 je .idle
 call terminal_script_window_hide
 mov [cs:choice],bx
.idle:
 call cooperative_show
 xor ax,ax
 ret
.begin:
 call terminal_script_window_open
 or ax,ax
 jnz .done
 mov word [cs:page],2
 mov word [cs:terminal_script_confirm_active],1
 mov word [cs:choice],1
 call paint
 xor ax,ax
.done:
 ret
.retire:
 call terminal_script_window_close
 xor ax,ax
 ret
.unowned:
 cmp bx,3
 je .retired
 mov ax,10
 ret
.retired:
 xor ax,ax
 ret
.operand:
 mov ax,7
 ret

; Maintained cooperative controller. The recovered blocking body below stays
; available as the original-behavior component, not the production scheduler.
; All state lives in this far code segment; redisplay_view is borrowed only
; while the terminal/command-menu owners are inactive.
terminal_script_window_open:
 cmp word [cs:terminal_script_window_active],0
 jne .state
 cmp word [terminal_aspect_active],1
 jne .state
 mov ax,[_redisplay_active]
 or ax,[_command_menu_active]
 jnz .state
 pushf
 pop ax
 test ax,0x200
 jz .state
 mov ax,[keyboard_debug_gate]
 mov [cs:old_context],ax
 mov word [keyboard_debug_gate],0x29
 mov word [cs:terminal_script_window_error],0
 mov word [cs:saved],0
 mov word [cs:page],0
 mov word [cs:terminal_script_window_active],1
 mov word [cs:terminal_script_window_cooperative],1
 call cooperative_show
 xor ax,ax
 ret
.state:
 mov ax,10
 ret

; Preserve the enclosing RPC's scalar argument, operation and result. The
; actual BBS frame/cursor is always exposed before any real parser/UI draw.
terminal_script_window_hide:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 cmp word [cs:terminal_script_window_cooperative],1
 jne .done
 cmp word [cs:saved],1
 jne .done
 mov ax,seg redisplay_view
 push ax
 mov ax,redisplay_view
 push ax
 push ax ; unused legacy descriptor, restore validates the far frame identity
 call local_window_restore
 add sp,6
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret

cooperative_show:
 cmp word [cs:saved],0
 jne .done
 call local_window_save
 call paint
.done:
 ret

terminal_script_window_close:
 call terminal_script_window_hide
 cmp word [cs:terminal_script_window_cooperative],1
 jne .done
 push ax
 mov ax,[cs:old_context]
 mov [keyboard_debug_gate],ax
 mov word [cs:terminal_script_window_cooperative],0
 mov word [cs:terminal_script_confirm_active],0
 mov word [cs:terminal_script_window_active],0
 pop ax
.done:
 ret

; BX=1 permits repaint at idle; BX=0 services keys while RX remains queued.
; No VM/WHEN work runs on this callback stack and no UART byte is consumed.
terminal_script_window_service:
 cmp word [cs:terminal_script_confirm_active],0
 je .admitted
 mov ax,10
 ret
.admitted:
 cmp word [cs:terminal_script_window_cooperative],1
 jne .done
 push bx
 call far terminal_script_window_keyboard_poll
 pop bx
 or ax,ax
 jz .idle
 ; Same low-byte and signed hook comparison as the recovered176-byte body.
 and ax,0xff
 jz .close
 cmp ax,0xe0
 je .close
 cmp ax,0x1c
 je .close
 cmp ax,0x1d
 je .close
 cmp ax,0x1f
 je .close
 cmp word [keyboard_mapping_hook_enabled],0
 je .consume
 mov dx,ax
 mov al,[keyboard_mapping_hook_character]
 cbw
 cmp ax,dx
 je .close
.consume:
 call far terminal_script_window_keyboard_read
.close:
 call terminal_script_window_close
 jmp .done
.idle:
 or bx,bx
 jz .done
 call cooperative_show
.done:
 xor ax,ax
 ret


terminal_script_window:
 push bp
 push si
 push di
 push es
 cmp word [cs:terminal_script_window_active],0
 jne .state
 cmp word [terminal_aspect_active],1
 jne .state
 mov ax,[_redisplay_active]
 or ax,[_command_menu_active]
 jnz .state
 pushf
 pop ax
 test ax,0x200
 jz .state
 mov ax,[keyboard_debug_gate]
 mov [cs:old_context],ax
 mov word [cs:terminal_script_window_error],0
 mov word [cs:saved],0
 mov word [cs:page],0
 mov word [cs:terminal_script_window_active],1
 call aspect_local_window
 mov ax,[cs:old_context]
 mov [keyboard_debug_gate],ax
 mov word [cs:terminal_script_window_active],0
 mov ax,[cs:terminal_script_window_error]
 jmp .done
.state:
 mov ax,10
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Original6530 consumes repeated Alt-Z before this debugger/window callback.
; Preserve all registers; CF distinguishes this owner from the old fail guard.
terminal_script_window_debug:
 cmp word [cs:terminal_script_confirm_active],0
 jne .unowned
 cmp word [cs:terminal_script_window_active],1
 jne .unowned
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 xor word [cs:page],1
 cmp word [cs:terminal_script_window_cooperative],1
 jne .paint
 cmp word [cs:saved],0
 je .hidden
.paint:
 call paint
.hidden:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 clc
 retf
.unowned:
 stc
 retf

; Full raw4000-byte frame; the metadata plane and parent parser never change.
; Native56FE preserves this returned far identity until its matching restore.
local_window_save:
 push es
 push si
 push di
 push cx
 mov bx,0xb800
 mov dx,seg redisplay_view
 mov di,redisplay_view
 xor si,si
 mov cx,2000
 call copy_frame
 pop cx
 pop di
 pop si
 pop es
 push bx
 mov ah,3
 xor bh,bh
 int 0x10
 mov [cs:old_cursor],dx
 mov [cs:old_shape],cx
 pop bx
 mov word [cs:saved],1
 mov ax,redisplay_view
 mov dx,seg redisplay_view
 ret
local_window_restore:
 push bp
 mov bp,sp
 cmp word [cs:saved],1
 jne .done
 cmp word [bp+6],redisplay_view
 jne .bad
 mov ax,seg redisplay_view
 cmp [bp+8],ax
 jne .bad
 jmp .restore
.bad:
 mov word [cs:terminal_script_window_error],10
.restore:
 mov ax,seg redisplay_view
 push es
 push si
 push di
 mov bx,ax
 mov si,redisplay_view
 mov dx,0xb800
 xor di,di
 mov cx,2000
 call copy_frame
 pop di
 pop si
 pop es
 xor bh,bh
 mov dx,[cs:old_cursor]
 mov ah,2
 int 0x10
 mov cx,[cs:old_shape]
 mov ah,1
 int 0x10
 mov word [cs:saved],0
.done:
 pop bp
 ret

; DS=SS throughout, with interrupts enabled for the child-owned UART. Switching
; ES per cell avoids an interrupt-visible foreign DS or an11ms CLI frame copy.
copy_frame:
 cld
.cell:
 mov es,bx
 mov ax,[es:si]
 mov es,dx
 stosw
 add si,2
 loop .cell
 ret
local_window_draw:
 call paint
 ret 6
local_window_keyboard_select:
 ret 2
local_window_write:
 ret 6
local_window_format:
 ret
local_window_status_draw:
 ret
local_window_key_read:
 call far terminal_script_window_keyboard_read
 ret
local_window_key_poll:
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 call terminal_script_window_poll
 or ax,ax
 jz .keyboard
 mov [cs:terminal_script_window_error],ax
 ; Low byte0 skips native64FE and exits through the matching frame restore.
 mov ax,0x100
 jmp .done
.keyboard:
 call far terminal_script_window_keyboard_poll
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret

paint:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0x1720
 mov cx,2000
 cld
 rep stosw
 mov si,reference
 cmp word [cs:page],2
 je .confirmation
 cmp word [cs:page],0
 je .line
 mov si,help
 jmp .line
.confirmation:
 mov si,confirm_no
 cmp word [cs:choice],2
 jne .line
 mov si,confirm_yes
.line:
 mov di,[cs:si]
 add si,2
 cmp di,0xffff
 je .hide
 mov ah,[cs:si]
 inc si
.text:
 mov al,[cs:si]
 inc si
 or al,al
 jz .line
 stosw
 jmp .text
.hide:
 mov ah,1
 mov cx,0x2000
 int 0x10
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret

%macro line 4
 dw 2*(80*%1+%2)
 db %3,%4,0
%endmacro
reference:
 line 2,6,0x5f,' PCPLUS  //  TERMINAL KEYS '
 line 5,6,0x1f,'Function and cursor keys use the selected keyboard profile.'
 line 7,6,0x17,'Ordinary typing continues the conversation while a script waits.'
 line 9,6,0x17,'Use the configured function keys for the remote system.'
 line 12,6,0x1f,'Alt-Z again: help / reference'
 line 14,6,0x17,'An ordinary key closes this window and is not sent.'
 line 16,6,0x17,'Local command keys remain queued for subsequent handling.'
 line 21,6,0x5f,' Escape: return to the script '
 dw 0xffff
help:
 line 2,6,0x5f,' PCPLUS  //  SCRIPT KEYBOARD HELP '
 line 5,6,0x1f,'Escape in this window dismisses the window.'
 line 7,6,0x17,'The running script continues while this window is open.'
 line 9,6,0x17,'Escape during an ordinary script wait asks to stop the script.'
 line 12,6,0x17,'Incoming data and terminal queries continue to be processed.'
 line 14,6,0x17,'The selected serial flow control remains active.'
 line 18,6,0x1f,'Alt-Z again: return to the key reference'
 line 21,6,0x5f,' Escape: return to the script '
 dw 0xffff
confirm_no:
 line 2,6,0x5f,' PCPLUS  //  STOP SCRIPT? '
 line 7,6,0x1f,'Stop the running script?'
 line 9,6,0x5f,' No '
 line 12,6,0x17,'Y: stop   N / Escape: continue   Enter: No'
 line 16,6,0x17,'Incoming data and terminal queries continue to be processed.'
 dw 0xffff
confirm_yes:
 line 2,6,0x5f,' PCPLUS  //  STOP SCRIPT? '
 line 7,6,0x1f,'Stop the running script?'
 line 9,6,0x5f,' Yes '
 dw 0xffff
terminal_script_window_cooperative: dw 0
terminal_script_window_active: dw 0
terminal_script_window_error: dw 0
old_context: dw 0
old_cursor: dw 0
old_shape: dw 0
saved: dw 0
page: dw 0
choice: dw 1
terminal_script_confirm_active: dw 0

; The linker bindings for unused native resource arguments use the initialized
; keyboard_debug_gate context word. Services above use their own static far
; frame/prose and never dereference those legacy arguments. No new near DATA.
