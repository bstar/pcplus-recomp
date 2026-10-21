; Test-only foreground rejection recorder. Original guard still returns3.
SEGMENT ASPECT_CODE
GLOBAL _aspect_render_diagnostic_reject
extern csi_terminal_id,screen_cursor_row,screen_cursor_column
extern screen_video_offset,screen_attribute_offset
extern connection_state,terminal_transfer_active,terminal_transfer_pending
extern _command_menu_script,terminal_program_pending
_aspect_render_diagnostic_reject:
 push bp
 mov bp,sp
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 mov ax,[bp+4]
 mov [cs:diag_record],ax
 %macro diag_word 2
 mov ax,[%2]
 mov [cs:diag_record+%1],ax
 %endmacro
 diag_word 2,csi_terminal_id
 diag_word 4,screen_cursor_row
 diag_word 6,screen_cursor_column
 diag_word 8,screen_video_offset
 diag_word 10,screen_attribute_offset
 diag_word 12,connection_state
 diag_word 14,terminal_parser_active
 diag_word 16,terminal_ansi_wait_active
 diag_word 18,terminal_transfer_active
 diag_word 20,terminal_transfer_pending
 diag_word 22,terminal_program_active
 diag_word 24,terminal_program_pending
 diag_word 26,terminal_aspect_active
 push cs
 pop es
 mov si,_command_menu_script
 mov di,diag_record+28
 mov cx,16
 rep movsb
 mov si,terminal_script_label
 mov di,diag_record+44
 mov cx,13
 rep movsb
 push cs
 pop ds
 mov dx,diag_path
 mov ax,0x3d02
 int 0x21
 jnc .opened
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc .done
.opened:
 mov bx,ax
 mov ax,0x4202
 xor cx,cx
 xor dx,dx
 int 0x21
 mov ah,0x40
 mov dx,diag_record
 mov cx,64
 int 0x21
 mov ah,0x3e
 int 0x21
.done:
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 pop bp
 mov ax,3
 ret
 diag_path: db 'D:\RGUARD.BIN',0
 diag_record: times 64 db 0
