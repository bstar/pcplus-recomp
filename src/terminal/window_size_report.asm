; Maintained XTWINOPS18 response, not original PCPlus code. DISPLAY_CODE owner.
; No cursor/mode/attribute/saved-state mutation. Foreground-only whole report
; reservation; UART ISR owns RX only. Full/bad queue silently refuses the reply.
BITS 16
CPU 8086
SEGMENT DISPLAY_CODE public align=16 class=FARCODE use16
global terminal_window_size_report
extern ansi_parameter_count,ansi_parameters,ansi_private,ansi_secondary
extern csi_row_count,csi_last_row,csi_column_count,screen_last_column,erase_cell_count
extern screen_columns,screen_video_row_bytes,text_video_segment,csi_terminal_id
extern terminal_quit,terminal_aspect_active,terminal_program_active,terminal_program_pending
extern terminal_transfer_active,terminal_transfer_pending,_terminal_row_geometry_active
extern terminal_tx_count,terminal_tx_head,terminal_tx_tail,terminal_tx_buffer
extern terminal_tx_origin_set_far
%macro restore 0
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
%endmacro
terminal_window_size_report:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 ; This dispatcher hook owns only the exact ordinary CSI18t query.
 cmp word [ansi_private],0
 jne .unmatched
 cmp word [ansi_secondary],0
 jne .unmatched
 cmp word [ansi_parameter_count],1
 jne .unmatched
 cmp word [ansi_parameters],18
 jne .unmatched
 mov ax,[terminal_quit]
 or ax,[terminal_aspect_active]
 or ax,[terminal_program_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_transfer_pending]
 or ax,[_terminal_row_geometry_active]
 jnz .handled
 mov ax,[csi_terminal_id]
 cmp ax,4
 je .profile
 cmp ax,6
 jne .handled
.profile:
 cmp word [screen_columns],80
 jne .handled
 cmp word [screen_video_row_bytes],160
 jne .handled
 cmp word [text_video_segment],0xb800
 jne .handled
 mov ax,[csi_row_count]
 cmp ax,1
 jb .handled
 cmp ax,50
 ja .handled
 dec ax
 cmp [csi_last_row],ax
 jne .handled
 mov ax,[csi_column_count]
 cmp ax,80
 je .columns
 cmp ax,132
 jne .handled
.columns:
 dec ax
 cmp [screen_last_column],ax
 jne .handled
 inc ax
 mul word [csi_row_count]
 or dx,dx
 jnz .handled
 cmp ax,4096
 ja .handled
 cmp [erase_cell_count],ax
 jne .handled
 mov di,response
 mov word [cs:di],0x5b1b
 mov word [cs:di+2],0x3b38
 add di,4
 mov ax,[csi_row_count]
 call decimal
 mov byte [cs:di],';'
 inc di
 mov ax,[csi_column_count]
 call decimal
 mov byte [cs:di],'t'
 inc di
 mov bp,di
 sub bp,response
 ; Count and ring relation are validated before copying any report byte.
 mov ax,[terminal_tx_count]
 cmp ax,1024
 ja .handled
 mov dx,1024
 sub dx,ax
 cmp dx,bp
 jb .handled
 mov bx,[terminal_tx_tail]
 cmp bx,1024
 jae .handled
 mov dx,[terminal_tx_head]
 cmp dx,1024
 jae .handled
 mov cx,bx
 sub cx,dx
 and cx,1023
 and ax,1023
 cmp cx,ax
 jne .handled
 mov si,response
 mov cx,bp
 xor dx,dx ; Dedicated/report bytes never become recorder user input.
.copy:
 mov al,[cs:si]
 mov [terminal_tx_buffer+bx],al
 call far terminal_tx_origin_set_far
 inc si
 inc bx
 and bx,1023
 loop .copy
 mov [terminal_tx_tail],bx
 add [terminal_tx_count],bp
.handled:
 restore
 stc
 retf
.unmatched:
 restore
 clc
 retf
decimal:
 mov bx,10
 xor cx,cx
.digit:
 xor dx,dx
 div bx
 push dx
 inc cx
 or ax,ax
 jnz .digit
.write:
 pop ax
 add al,'0'
 mov [cs:di],al
 inc di
 loop .write
 ret
response: times 16 db 0
