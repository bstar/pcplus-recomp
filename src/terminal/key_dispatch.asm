; Shared terminal/ASPECT profile output. Classification remains the actual
; parent raw classifier; only the admitted child owns UART during a script.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern keyboard_classify_raw,terminal_enqueue_al,terminal_receive_character
extern screen_cursor_up,screen_cursor_down,screen_cursor_left,screen_cursor_right,screen_set_cursor
global terminal_key_classify_far,terminal_key_emit_far,terminal_key_echo_far,terminal_key_cursor_far
terminal_key_classify_far:
 call keyboard_classify_raw
 retf
terminal_key_emit_far:
 call terminal_enqueue_al
 retf
terminal_key_echo_far:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 push ax
 call terminal_receive_character
 add sp,2
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
; AX1up,2down,3left,4right,5native home(0,0). No UART or BIOS keyboard read.
terminal_key_cursor_far:
 cmp ax,1
 je .up
 cmp ax,2
 je .down
 cmp ax,3
 je .left
 cmp ax,4
 je .right
 xor ax,ax
 xor dx,dx
 call screen_set_cursor
 retf
.up: call screen_cursor_up
 retf
.down: call screen_cursor_down
 retf
.left: call screen_cursor_left
 retf
.right: call screen_cursor_right
 retf

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern terminal_keymap,modes_value_1d1a,terminal_aspect_active
extern terminal_tx_count,terminal_quit,terminal_exit_code
extern terminal_key_edit_admit_far,terminal_key_edit_far
extern terminal_key_reverse_tab_admit_far,terminal_key_reverse_tab_far
global terminal_key_output
; AX raw normalized key; BX effective duplex byte,FFFF=parent selection.
; Return typed ASPECT0/3/7/14. BP/SI/DI/ES preserved, BX/CX/DX/flags scratch.
; Validate binding and echo support before any output. A local key is never
; substituted with its scan byte. Unsupported half-duplex editing is explicit.
terminal_key_output:
 push bp
 push si
 push di
 push es
 mov di,bx
 cmp di,0xffff
 je .inherited
 cmp di,255
 jbe .duplex
 mov ax,7
 jmp .done
.inherited:
 mov di,[modes_value_1d1a]
.duplex:
 ; Maintained compatibility aliases also used by terminal_read_key.
 cmp ax,0x1ce0
 jne .slash
 mov ax,0xe00d
.slash:
 cmp ax,0x35e0
 jne .local_keys
 mov ax,0xe02f
.local_keys:
 ; Maintained local commands override original no-op/unmapped classifications.
 cmp ax,0x7000
 je .unsupported
 cmp ax,0x8300
 je .unsupported
 cmp ax,0xfe00
 je .unsupported
 call far terminal_key_classify_far
 cmp ax,79
 jb .binding
 cmp ah,1
 je .literal
 cmp ax,0xffff
 je .success
 jmp .unsupported
.literal:
 mov bp,ax
 or di,di
 jz .literal_send
 cmp al,27
 je .literal_send
 xor ah,ah
 call far terminal_key_echo_far
.literal_send:
 mov ax,bp
 xor ah,ah
 call far terminal_key_emit_far
 jmp .success
.binding:
 mov bp,ax
.locate:
 mov bx,12
 mul bx
 mov si,terminal_keymap
 add si,ax
 mov bx,si
 xor cx,cx
.bound:
 cmp byte [bx],0
 je .capacity
 inc bx
 inc cx
 cmp cx,12
 jb .bound
 mov ax,7
 jmp .done
.capacity:
 or di,di
 jz .queue_capacity
 cmp bp,7
 jne .edit_check
 call far terminal_key_reverse_tab_admit_far
 or ax,ax
 jnz .done
 jmp .queue_capacity
.edit_check:
 xor ax,ax
 cmp bp,8
 je .edit_admit
 cmp bp,54
 je .edit_admit
 inc ax
 cmp bp,9
 je .edit_admit
 cmp bp,55
 jne .queue_capacity
.edit_admit:
 call far terminal_key_edit_admit_far
 or ax,ax
 jnz .done
.queue_capacity:
 cmp word [terminal_aspect_active],0
 jne .send_start
 mov dx,1024
 sub dx,[terminal_tx_count]
 jc .overflow
 cmp dx,cx
 jb .overflow
.send_start:
 push si
 jcxz .sent
.send:
 lodsb
 xor ah,ah
 cmp al,0xff
 jne .wire
 xor ax,ax
.wire:
 call far terminal_key_emit_far
 loop .send
.sent:
 pop si
 or di,di
 jz .success
 cmp bp,6
 jbe .echo_string
 cmp bp,28
 jb .special_echo
 cmp bp,37
 jbe .echo_string
 cmp bp,78
 je .echo_string
.special_echo:
 cmp bp,7
 je .reverse_tab
 xor ax,ax
 cmp bp,8
 je .edit
 cmp bp,54
 je .edit
 inc ax
 cmp bp,9
 je .edit
 cmp bp,55
 je .edit
 cmp bp,10
 je .backspace
 mov ax,1
 cmp bp,50
 je .cursor
 cmp bp,72
 je .cursor
 inc ax
 cmp bp,51
 je .cursor
 cmp bp,73
 je .cursor
 inc ax
 cmp bp,52
 je .cursor
 cmp bp,74
 je .cursor
 inc ax
 cmp bp,53
 je .cursor
 cmp bp,75
 je .cursor
 inc ax
 cmp bp,76
 jne .success
.cursor:
 call far terminal_key_cursor_far
 jmp .success
.backspace:
 mov ax,8
 call far terminal_key_echo_far
 jmp .success
.edit:
 call far terminal_key_edit_far
 jmp .success
.reverse_tab:
 call far terminal_key_reverse_tab_far
 jmp .success
.echo_string:
 ; Native3ADB echoes stored FF as FF; only wire emission translates it to NUL.
 lodsb
 or al,al
 jz .success
 xor ah,ah
 call far terminal_key_echo_far
 jmp .echo_string
.overflow:
 mov word [terminal_exit_code],3
 mov word [terminal_quit],1
 mov ax,14
 jmp .done
.unsupported:
 mov ax,3
 jmp .done
.success:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 retf
