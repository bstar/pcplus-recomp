; Maintained80-column transfer prompt/progress. Own bottomtwo physical rows;
; composed row geometry admits25/28/43/50 and binds the restore lease. No DOSIO.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern terminal_transfer_ui_service_far,terminal_transfer_fault,terminal_quit
extern terminal_transfer_ui_keyboard_far,terminal_transfer_ui_read_far,terminal_transfer_filename
extern session_blocks_accepted
extern terminal_transfer_direction,terminal_upload_blocks_accepted
extern terminal_transfer_protocol,_ymodem_current
extern _terminal_zmodem_kbytes
extern terminal_transfer_automatic
%ifdef TERMINAL_ROW_GEOMETRY
extern _terminal_row_status_layout,ui_window_rows,csi_column_count,screen_attribute_row_bytes
extern terminal_exit_code
%endif
%macro ui_top 0
%ifdef TERMINAL_ROW_GEOMETRY
 mov di,[cs:transfer_ui_base]
%else
 mov di,3680
%endif
%endmacro
%macro ui_field_offset 0
%ifdef TERMINAL_ROW_GEOMETRY
 add di,[cs:transfer_ui_base]
 add di,160
%else
 add di,3840
%endif
%endmacro
GLOBAL terminal_transfer_ui_open_impl,terminal_transfer_ui_restore_impl,terminal_transfer_ui_progress_impl
GLOBAL terminal_transfer_ui_receiving_impl
GLOBAL _terminal_transfer_ui_visible
terminal_transfer_ui_open_impl:
 push bp
 push bx
 push si
 push di
 push es
%ifdef TERMINAL_ROW_GEOMETRY
 cmp byte [transfer_ui_visible],0
 jne .bad_view
 call transfer_ui_layout
 jc .bad_view
 mov [cs:transfer_ui_base],ax
 mov [cs:transfer_ui_last_row],dl
%else
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .bad_view
 cmp ah,80
 jne .bad_view
 or bh,bh
 jnz .bad_view
%endif
 mov ah,3
 xor bh,bh
 int 0x10
global terminal_transfer_ui_cursor_read_site
terminal_transfer_ui_cursor_read_site equ $
 mov [transfer_ui_cursor],dx
 mov [transfer_ui_shape],cx
 push ds
 mov ax,0xb800
 mov ds,ax
%ifdef TERMINAL_ROW_GEOMETRY
 mov si,[cs:transfer_ui_base]
%else
 mov si,3680
%endif
 pop es
 mov di,transfer_ui_saved
 mov cx,160
 cld
 rep movsw
 push es
 pop ds
 mov byte [transfer_ui_visible],1
 mov ax,0xb800
 mov es,ax
 ui_top
 mov ax,0x1f20
 mov cx,160
 rep stosw
 call ui_title
 cmp word [terminal_transfer_automatic],1
 jne .manual
 mov ax,1
 jmp .done
.manual:
 mov word [transfer_ui_length],0
 mov byte [terminal_transfer_filename],0
 mov cx,0x0607
 mov ah,1
 int 0x10
.input:
 call ui_cursor
 call far terminal_transfer_ui_service_far
 cmp word [terminal_transfer_fault],0
 jne .cancel
 call far terminal_transfer_ui_keyboard_far
 or ax,ax
 jz .input
 call far terminal_transfer_ui_read_far
 cmp ax,0x3c00 ;F2 toggles protocol, typed field retained
 je .protocol
 cmp ax,0x2d00
 je .quit
 cmp al,27
 je .cancel
 cmp al,13
 je .accept
 cmp al,8
 je .backspace
 cmp al,32
 jb .input
 cmp al,126
 ja .input
 mov bx,[transfer_ui_length]
 cmp bx,63
 jae .input
 mov [terminal_transfer_filename+bx],al
 mov di,bx
 shl di,1
 ui_field_offset
 mov ah,0x1f
 mov [es:di],ax
 inc bx
 mov [transfer_ui_length],bx
 mov byte [terminal_transfer_filename+bx],0
 jmp .input
.protocol:
 inc word [terminal_transfer_protocol]
 cmp word [terminal_transfer_protocol],3
 jb .selected
 mov word [terminal_transfer_protocol],0
.selected:
 call ui_title
 jmp .input
.backspace:
 mov bx,[transfer_ui_length]
 or bx,bx
 jz .input
 dec bx
 mov [transfer_ui_length],bx
 mov byte [terminal_transfer_filename+bx],0
 mov di,bx
 shl di,1
 ui_field_offset
 mov word [es:di],0x1f20
 jmp .input
.accept:
 cmp word [transfer_ui_length],0
 je .input
 mov ax,1
 jmp .done
.quit:
 mov word [terminal_quit],1
.cancel:
 cmp word [terminal_transfer_fault],0
 jne .canceled
 mov word [terminal_transfer_fault],2
.canceled:
 xor ax,ax
 jmp .done
.bad_view:
 mov word [terminal_transfer_fault],8
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 retf
ui_cursor:
 mov dx,[transfer_ui_length]
%ifdef TERMINAL_ROW_GEOMETRY
 mov dh,[cs:transfer_ui_last_row]
%else
 mov dh,24
%endif
 xor bh,bh
 mov ah,2
 int 0x10
global terminal_transfer_ui_prompt_cursor_site
terminal_transfer_ui_prompt_cursor_site equ $
 ret
ui_title:
 mov ax,0x1f20
 ui_top
 mov cx,80
 rep stosw
 mov si,transfer_ui_title
 cmp word [terminal_transfer_direction],1
 jne .protocol
 mov si,transfer_ui_upload_title
.protocol:
 cmp word [terminal_transfer_protocol],2
 je .zmodem_title
 cmp word [terminal_transfer_protocol],1
 jne .draw
 mov si,transfer_ui_batch_title
 cmp word [terminal_transfer_direction],1
 jne .draw
 mov si,transfer_ui_batch_upload_title
 jmp .draw
.zmodem_title:
 mov si,transfer_ui_zmodem_title
 cmp word [terminal_transfer_direction],1
 jne .draw
 mov si,transfer_ui_zmodem_upload_title
.draw:
 ui_top
 call ui_text
 ret
ui_text:
 lodsb
 or al,al
 jz .done
 mov ah,0x1f
 stosw
 jmp ui_text
.done: ret
terminal_transfer_ui_receiving_impl:
 push ax
 push cx
 push si
 push di
 push es
 mov ax,0xb800
 mov es,ax
 ui_top
 mov ax,0x1f20
 mov cx,80
 rep stosw
 mov si,transfer_ui_running
 cmp word [terminal_transfer_direction],1
 jne .running
 mov si,transfer_ui_upload_running
.running:
 cmp word [terminal_transfer_protocol],2
 je .zmodem_running
 cmp word [terminal_transfer_protocol],1
 jne .draw
 mov si,transfer_ui_batch_running
 cmp word [terminal_transfer_direction],1
 jne .draw
 mov si,transfer_ui_batch_upload_running
 jmp .draw
.zmodem_running:
 mov si,transfer_ui_zmodem_running
 cmp word [terminal_transfer_direction],1
 jne .draw
 mov si,transfer_ui_zmodem_upload_running
.draw:
 ui_top
 call ui_text
 pop es
 pop di
 pop si
 pop cx
 pop ax
 retf
terminal_transfer_ui_progress_impl:
 push ax
 push bx
 push cx
 push dx
 push di
 push es
 mov ax,0xb800
 mov es,ax
%ifdef TERMINAL_ROW_GEOMETRY
 ui_top
 add di,70*2
%else
 mov di,3680+70*2
%endif
 mov ax,[session_blocks_accepted]
 cmp word [terminal_transfer_direction],1
 jne .count
 mov ax,[terminal_upload_blocks_accepted]
.count:
 cmp word [terminal_transfer_protocol],2
 jne .batch_count
 mov ax,[_terminal_zmodem_kbytes]
 jmp .digits
.batch_count:
 cmp word [terminal_transfer_protocol],1
 jne .digits
 mov ax,[_ymodem_current+6] ;fixed nearC word blocks
.digits:
 mov bx,10
 mov cx,5
.digit:
 xor dx,dx
 div bx
 add dl,'0'
 mov dh,0x1f
 mov [es:di],dx
 sub di,2
 loop .digit
 pop es
 pop di
 pop dx
 pop cx
 pop bx
 pop ax
 retf
terminal_transfer_ui_restore_impl:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cmp byte [transfer_ui_visible],0
 je .done
%ifdef TERMINAL_ROW_GEOMETRY
 call transfer_ui_layout
 jc .bad_restore
 cmp ax,[cs:transfer_ui_base]
 jne .bad_restore
 cmp dl,[cs:transfer_ui_last_row]
 jne .bad_restore
%endif
 mov ax,0xb800
 mov es,ax
 mov si,transfer_ui_saved
 ui_top
 mov cx,160
 rep movsw
global terminal_transfer_ui_restored_cells_site
terminal_transfer_ui_restored_cells_site equ $
 mov cx,[transfer_ui_shape]
 mov ah,1
 int 0x10
 mov dx,[transfer_ui_cursor]
 xor bh,bh
 mov ah,2
 int 0x10
 mov byte [transfer_ui_visible],0
%ifdef TERMINAL_ROW_GEOMETRY
 jmp .done
.bad_restore:
 ; The old lease no longer describes this display. Do not replay cells or
 ; cursor metadata into another mode/height, and do not resume mixed parsing.
 mov byte [transfer_ui_visible],0
 cmp word [terminal_transfer_fault],0
 jne .fatal
 mov word [terminal_transfer_fault],8
.fatal:
 mov word [terminal_quit],1
 cmp word [terminal_exit_code],0
 jne .done
 mov word [terminal_exit_code],7
%endif
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
%ifdef TERMINAL_ROW_GEOMETRY
; Read-only admission. AX=top byte offset, DX=last physical row, CF0 admitted.
; All nonstack storage remains untouched. DS=SS, IF1/DF0, narrow canonical
; geometry and real BIOS mode/page/height must agree before acquisition/replay.
transfer_ui_layout:
 push bx
 push cx
 push si
 push di
 push bp
 push es
 mov bx,ds
 mov cx,ss
 cmp bx,cx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 call far _terminal_row_status_layout
 or ax,ax
 jnz .bad
 cmp word [csi_column_count],80
 jne .bad
 cmp word [screen_attribute_row_bytes],80
 jne .bad
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .bad
 cmp ah,80
 jne .bad
 or bh,bh
 jnz .bad
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 or ax,ax
 jz .legacy25
 inc ax
 jmp .height
.legacy25:
 mov ax,25
.height:
 cmp ax,[ui_window_rows]
 jne .bad
 sub ax,2
 mov dx,160
 mul dx
 mov dx,[ui_window_rows]
 dec dx
 clc
 jmp .done
.bad:
 stc
.done:
 pop es
 pop bp
 pop di
 pop si
 pop cx
 pop bx
 ret
transfer_ui_base: dw 0
transfer_ui_last_row: db 0
%endif
SEGMENT _DATA public class=DATA use16
transfer_ui_saved: times 320 db 0
transfer_ui_cursor: dw 0
transfer_ui_shape: dw 0
transfer_ui_length: dw 0
_terminal_transfer_ui_visible:
transfer_ui_visible: db 0
transfer_ui_title: db ' Download: XMODEM   [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_running: db ' Receiving XMODEM   [Esc] Cancel                    Blocks:',0
transfer_ui_upload_title: db ' Upload: XMODEM/1K   [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_upload_running: db ' Sending XMODEM/1K  [Esc] Cancel                    Blocks:',0
transfer_ui_batch_title: db ' YMODEM directory:  [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_batch_upload_title: db ' YMODEM filespec:   [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_batch_running: db ' Receiving YMODEM  [Esc] Cancel                    Blocks:',0
transfer_ui_batch_upload_running: db ' Sending YMODEM    [Esc] Cancel                    Blocks:',0
transfer_ui_zmodem_title: db ' ZMODEM directory: [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_zmodem_upload_title: db ' ZMODEM filespec:  [F2] Protocol   [Enter] Start   [Esc] Cancel',0
transfer_ui_zmodem_running: db ' Receiving ZMODEM [Esc] Cancel                       KiB:',0
transfer_ui_zmodem_upload_running: db ' Sending ZMODEM   [Esc] Cancel                       KiB:',0
