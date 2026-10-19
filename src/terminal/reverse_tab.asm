; Shared keyboard reverse Tab: readonly preflight then exact recovered code.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern keyboard_reverse_tab,attribute_geometry_admit,terminal_reset_protected_home
extern terminal_tab_stops,terminal_tab_wrap,terminal_tab_mode_8ff8,scroll_skip_attribute_scan
extern screen_cursor_wrap,screen_attribute_checks,screen_reverse_wrap_blocked
extern screen_cursor_row,screen_cursor_column,screen_first_row,screen_last_row
extern screen_attribute_offset,screen_attribute_cells,screen_line_flags,erase_cell_count
extern scroll_enabled,scroll_suppress_next_linefeed
global terminal_key_reverse_tab_admit_far,terminal_key_reverse_tab_far,reverse_tab_protected_home

terminal_key_reverse_tab_admit_far:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call attribute_geometry_admit
 jc .reject
 cmp word [screen_cursor_wrap],0
 je .plain_table
 cmp word [screen_attribute_checks],0
 jne .protected
 ; Native table scans are unbounded. Require a sorted, FE-terminated prefix.
.plain_table:
 mov si,terminal_tab_stops
 mov cx,30
 xor bx,bx
 xor di,di
.table:
 lodsb
 cmp al,0xfe
 je .table_ready
 cmp al,80
 jae .reject
 or di,di
 jz .first
 cmp al,bl
 jbe .reject
.first:
 mov bl,al
 inc di
 loop .table
 jmp .reject
.table_ready:
.plain:
 ; Recursion is reachable only from column0 with a populated table and one
 ; of these native reverse-wrap policies. The real cursor-left must advance.
 or di,di
 jz .admit
 cmp word [screen_cursor_column],0
 jne .admit
 mov ax,[terminal_tab_wrap]
 or ax,[scroll_skip_attribute_scan]
 jz .admit
 cmp word [screen_cursor_wrap],0
 je .reject
 call .left_can_wrap
 jc .reject
 jmp .admit
.protected:
 ; Predict only admission. The actual screen changes still run native code.
 mov si,[screen_attribute_offset]
 mov ax,[screen_cursor_column]
 or ax,ax
 jz .protected_wrap
 mov bx,[screen_cursor_row]
 test byte [screen_line_flags+bx],0x40
 jz .one_left
 cmp ax,1
 je .reject
 dec si
.one_left:
 dec si
 jmp .left_boundary
.protected_wrap:
 mov ax,[screen_cursor_row]
 cmp ax,[screen_first_row]
 jne .previous_row
 cmp word [screen_reverse_wrap_blocked],0
 jne .core_boundary
 mov ax,[screen_last_row]
 mov bx,80
 mul bx
 add ax,79
 mov si,ax
 jmp .left_boundary
.previous_row:
 or ax,ax
 jz .reject
 dec si
.left_boundary:
 call .backward_unprotected
.core_boundary:
 or si,si
 jnz .check_boundary
 cmp word [screen_reverse_wrap_blocked],0
 jne .admit
.check_boundary:
 call .backward_unprotected
.find_marker:
 or si,si
 jz .admit
 test byte [screen_attribute_cells+si],0x81
 jnz .marker
 dec si
 jmp .find_marker
.marker:
 mov ax,si
 xor dx,dx
 mov bx,80
 div bx
 cmp dx,79
 jne .admit
 ; A native Right at this marker wraps. Suppressed linefeed leaves offsets
 ; stale, and protected scrolling reaches unrecovered attribute-repair APIs.
 cmp word [scroll_suppress_next_linefeed],0
 jne .reject
 cmp ax,[screen_last_row]
 jne .admit
 cmp word [scroll_enabled],0
 jne .reject
.admit:
 xor ax,ax
 jmp .done
.reject:
 mov ax,3
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

.left_can_wrap:
 mov ax,[screen_cursor_row]
 cmp ax,[screen_first_row]
 jne .not_first
 cmp word [screen_reverse_wrap_blocked],0
 jne .cannot
 clc
 ret
.not_first:
 or ax,ax
 jz .cannot
 clc
 ret
.cannot:
 stc
 ret

; Native boundary's backward circular search, read-only and explicitly bounded.
.backward_unprotected:
 mov cx,[erase_cell_count]
.back:
 test byte [screen_attribute_cells+si],0x81
 jz .back_done
 or si,si
 jnz .decrement
 mov si,[erase_cell_count]
.decrement:
 dec si
 loop .back
 xor si,si
.back_done:
 ret

terminal_key_reverse_tab_far:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 call keyboard_reverse_tab
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
reverse_tab_protected_home:
 jmp terminal_reset_protected_home
