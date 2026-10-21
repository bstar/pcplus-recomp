; Maintained80x25 transfer prompt/progress. Own bottomtwo rows only; no DOSIO.
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
GLOBAL terminal_transfer_ui_open_impl,terminal_transfer_ui_restore_impl,terminal_transfer_ui_progress_impl
GLOBAL terminal_transfer_ui_receiving_impl
GLOBAL _terminal_transfer_ui_visible
terminal_transfer_ui_open_impl:
 push bp
 push bx
 push si
 push di
 push es
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .bad_view
 cmp ah,80
 jne .bad_view
 or bh,bh
 jnz .bad_view
 mov ah,3
 xor bh,bh
 int 0x10
 mov [transfer_ui_cursor],dx
 mov [transfer_ui_shape],cx
 push ds
 mov ax,0xb800
 mov ds,ax
 mov si,3680
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
 mov di,3680
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
 add di,3840
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
 add di,3840
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
 mov dh,24
 xor bh,bh
 mov ah,2
 int 0x10
 ret
ui_title:
 mov ax,0x1f20
 mov di,3680
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
 mov di,3680
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
 mov di,3680
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
 mov di,3680
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
 mov di,3680+70*2
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
 mov ax,0xb800
 mov es,ax
 mov si,transfer_ui_saved
 mov di,3680
 mov cx,160
 rep movsw
 mov cx,[transfer_ui_shape]
 mov ah,1
 int 0x10
 mov dx,[transfer_ui_cursor]
 xor bh,bh
 mov ah,2
 int 0x10
 mov byte [transfer_ui_visible],0
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
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
