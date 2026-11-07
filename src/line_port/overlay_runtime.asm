; Matched-parent transient Line/Port bank. DS=SS throughout every callback.
; File reads/CRC are bounded to512 bytes per foreground turn; no allocation.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern process_psp,terminal_quit,terminal_exit_code,_resource_program_path
extern _line_overlay_arena_ready
extern _line_port_bank_event,_line_port_bank_cursor,_line_port_bank_run
extern _line_port_bank_poll,_line_port_bank_busy
global _line_port_front_event,_line_port_front_cursor,_line_port_front_run,_line_port_front_poll
global _line_port_front_pending
global _line_overlay_expected,_line_overlay_state
_line_overlay_expected: dw 0x504c,0x314f,0,0,0,0,0,0
%define bytes _line_overlay_expected
%define relocs _line_overlay_expected+2
%define crc_lo _line_overlay_expected+4
%define crc_hi _line_overlay_expected+6
%define target _line_overlay_expected+8
%define data_seg _line_overlay_expected+10
%define usage_offset _line_overlay_expected+12
%define usage_bytes _line_overlay_expected+14
_line_overlay_state: times 16 dw 0
%define phase _line_overlay_state
%define stage _line_overlay_state+2
%define handle _line_overlay_state+4
%define at _line_overlay_state+6
%define fix _line_overlay_state+8
%define busy _line_overlay_state+10
%define fatal _line_overlay_state+12
%define crc _line_overlay_state+14
%define frame _line_overlay_state+18
%define reason _line_overlay_state+22
%define last_base _line_overlay_state+24
%define last_segment _line_overlay_state+26
%define last_offset _line_overlay_state+28
%define dirty _line_overlay_state+30
leaf: db 'PCLINE.OVL',0
loading: db 'Loading Line/Port... Esc cancels.',0
failed: db 'Line/Port module unavailable or mismatched. Esc returns.',0
recovery: db 'Line/Port module close failed. Esc exits to DOS.',0
usage_missing: db 'Cannot read PCLINE.OVL.',13,10,'$'
_line_port_front_pending:
 xor ax,ax
 cmp word [cs:phase],1
 jne .done
 inc ax
.done:retf

; CF0/AX=handle, CF1=unavailable. Caller supplies DS=SS. Path/leaf use only
; bounded private stack storage; opening never depends on the current drive.
open_module:
 push bp
 mov bp,sp
 push cx
 push dx
 push si
 push di
 sub sp,80
 mov di,sp
 mov si,leaf
 mov cx,11
.leaf:
 mov al,[cs:si]
 mov [di],al
 inc si
 inc di
 loop .leaf
 mov dx,sp
 mov di,dx
 add di,14
 push di
 push dx
 push word [process_psp]
 call _resource_program_path
 add sp,6
 or ax,ax
 jnz .bad
 mov dx,di
 mov ax,0x3da0
 int 0x21
 jmp .done
.bad:stc
.done:
 lea sp,[bp-8]
 pop di
 pop si
 pop dx
 pop cx
 pop bp
 ret

; Startup-only help data. Stream the original DOS09 span without its trailing
; dollar. No code entry, allocation, persistent buffer or configured UART use.
global terminal_usage_stream
terminal_usage_stream:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 mov bp,sp
 sub sp,128
 call open_module
 jc .failed
 mov di,ax
 mov bx,ax
 xor cx,cx
 mov dx,[cs:usage_offset]
 mov ax,0x4200
 int 0x21
 jc .close_failed
 mov si,[cs:usage_bytes]
.read:
 or si,si
 jz .close
 mov cx,si
 cmp cx,128
 jbe .counted
 mov cx,128
.counted:
 mov bx,di
 mov dx,sp
 mov ah,0x3f
 int 0x21
 jc .close_failed
 cmp ax,cx
 jne .close_failed
 sub si,ax
 mov cx,ax
 mov bx,1
 mov dx,sp
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,cx
 jne .close_failed
 jmp .read
.close:
 mov bx,di
 mov ah,0x3e
 int 0x21
 jc .failed
 clc
 jmp .done
.close_failed:
 mov bx,di
 mov ah,0x3e
 int 0x21
.failed:
 push cs
 pop ds
 mov dx,usage_missing
 mov ah,9
 int 0x21
 stc
.done:
 mov sp,bp
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

_line_port_front_cursor:
 cmp word [cs:phase],2
 je .bank
 mov ax,0xffff
 cmp word [cs:phase],0
 je .done
 mov ax,0x1243
.done:retf
.bank:jmp far _line_port_bank_cursor
_line_port_front_run:
 cmp word [cs:phase],2
 je .bank
 mov ax,1
 retf
.bank:jmp far _line_port_bank_run

; AX=load base, DX=arena segment. No DS changes and no inferred PSP address.
arena:
 mov ax,ss
 sub ax,[cs:data_seg]
 mov dx,ax
 add dx,[cs:target]
 ret
close_file:
 mov bx,[cs:handle]
 cmp bx,0xffff
 je .done
 mov ah,0x3e
 int 0x21
 jnc .closed
 mov word [cs:fatal],1
.closed:mov word [cs:handle],0xffff
.done:ret
error:
 call close_file
 mov word [cs:phase],3
 mov word [cs:dirty],1
 ret

_line_port_front_event:
 push bp
 mov bp,sp
 cmp word [cs:phase],2
 jne .local
 cmp word [bp+6],3
 jne .tail
 cmp word [cs:dirty],0
 jne .local
.tail:
 pop bp
 jmp far _line_port_bank_event
.local:
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 cld
 mov ax,[bp+6]
 cmp ax,3
 jne .not_idle
 cmp word [cs:dirty],0
 jne .paint_idle
 mov ax,2
 jmp .done
.paint_idle:
 mov word [cs:dirty],0
 cmp word [cs:phase],2
 jne .draw
 push word [bp+12]
 push word [bp+10]
 xor ax,ax
 push ax
 mov ax,2
 push ax
 call far _line_port_bank_event
 add sp,8
 jmp .one
.not_idle:
 cmp ax,0
 je .begin
 cmp ax,4
 je .stop
 cmp ax,1
 jne .not_key
 cmp byte [bp+8],27
 je .stop
 jmp .one
.not_key:
 cmp ax,2
 je .draw
 jmp .one
.stop:
 call close_file
 cmp word [cs:fatal],0
 je .stopped
 mov word [terminal_exit_code],14
 mov word [terminal_quit],1
.stopped:
 mov word [cs:phase],0
 xor ax,ax
 jmp .done
.begin:
 cmp word [cs:fatal],0
 jne .draw
 mov word [cs:phase],1
 mov word [cs:handle],0xffff
 xor ax,ax
 mov [cs:stage],ax
 mov [cs:at],ax
 mov [cs:fix],ax
 mov [cs:busy],ax
 mov [cs:dirty],ax
 mov [cs:reason],ax
 mov word [cs:crc],0xffff
 mov word [cs:crc+2],0xffff
 mov ax,[bp+10]
 mov [cs:frame],ax
 mov ax,[bp+12]
 mov [cs:frame+2],ax
 call far _line_overlay_arena_ready
 or ax,ax
 jz .bad_begin
 cmp word [cs:bytes],0
 je .bad_begin
 cmp word [cs:bytes],24000
 ja .bad_begin
 cmp word [cs:relocs],512
 ja .bad_begin
 call arena
 add dx,2048
 jc .bad_begin
 cmp dx,0xa000
 ja .bad_begin
 call open_module
 jc .bad_begin
 mov [cs:handle],ax
 jmp .draw
.bad_begin:
 call error
.draw:
 les di,[bp+10]
 add di,3200
 mov cx,80
 mov ax,0x0720
 rep stosw
 sub di,158
 mov si,loading
 cmp word [cs:phase],1
 je .text
 mov si,failed
 cmp word [cs:fatal],0
 je .text
 mov si,recovery
.text:
 mov al,[cs:si]
 inc si
 or al,al
 jz .one
 mov ah,0x0f
 stosw
 jmp .text
.one:mov ax,1
.done:
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

_line_port_front_poll:
 cmp word [cs:busy],0
 jne .quick
 cmp word [cs:phase],2
 je .bank
 cmp word [cs:phase],1
 je .load
.quick:retf
.bank:
 mov word [cs:busy],1
 call far _line_port_bank_poll
 call far _line_port_bank_busy
 or ax,ax
 jnz .bank_done
 mov word [cs:phase],0
.bank_done:
 mov word [cs:busy],0
 retf
.load:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 cld
 mov word [cs:busy],1
 call arena
 mov bp,ax
 mov es,dx
 cmp word [cs:stage],0
 jne .fixups
 mov si,[cs:relocs]
 shl si,1
 add si,[cs:bytes]
 sub si,[cs:at]
 jz .eof
 cmp si,512
 jbe .read
 mov si,512
.read:
 mov bx,[cs:handle]
 mov dx,[cs:at]
 mov cx,si
 push es
 pop ds
 mov ah,0x3f
 int 0x21
 push ss
 pop ds
 jc .bad
 cmp ax,si
 jne .bad
 push si
 push es
 push word [cs:at]
 push word [cs:crc+2]
 push word [cs:crc]
 call crc_block
 add sp,10
 mov [cs:crc],ax
 mov [cs:crc+2],dx
 add [cs:at],si
 jmp .done
.eof:
 mov bx,[cs:handle]
 mov dx,[cs:at]
 mov cx,1
 push es
 pop ds
 mov ah,0x3f
 int 0x21
 push ss
 pop ds
 jc .bad
 or ax,ax
 jnz .bad
 call close_file
 cmp word [cs:fatal],0
 jne .bad
 mov ax,[cs:crc]
 mov dx,[cs:crc+2]
 not ax
 not dx
 cmp ax,[cs:crc_lo]
 jne .bad
 cmp dx,[cs:crc_hi]
 jne .bad
 mov word [cs:stage],1
.fixups:
 mov di,[cs:fix]
 mov cx,32
.fix:
 cmp di,[cs:relocs]
 jae .ready
 mov bx,di
 shl bx,1
 add bx,[cs:bytes]
 mov si,[es:bx]
 mov ax,[cs:bytes]
 dec ax
 cmp si,ax
 jae .bad
 or di,di
 jz .ordered
 cmp si,[es:bx-2]
 jbe .bad
.ordered:
 mov ax,[es:si]
 add ax,bp
 jc .bad
 cmp ax,0xa000
 jae .bad
 mov [es:si],ax
 inc di
 mov [cs:fix],di
 loop .fix
 jmp .done
.ready:
 mov word [cs:phase],2
 push word [cs:frame+2]
 push word [cs:frame]
 xor ax,ax
 push ax
 xor ax,ax
 push ax
 call far _line_port_bank_event
 add sp,8
 mov word [cs:dirty],1
 jmp .done
.bad:
 call error
.done:
 mov word [cs:busy],0
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

; Standard reflected CRC32. Near cdecl, DX:AX return, DS restored exactly.
crc_block:
 push bp
 mov bp,sp
 push bx
 push cx
 push si
 push ds
 mov ax,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+12]
 lds si,[bp+8]
 jcxz .done
.byte:
 xor al,[si]
 inc si
 mov bx,8
.bit:
 shr dx,1
 rcr ax,1
 jnc .plain
 xor dx,0xedb8
 xor ax,0x8320
.plain:
 dec bx
 jnz .bit
 loop .byte
.done:
 pop ds
 pop si
 pop cx
 pop bx
 pop bp
 ret

%ifdef TERMINAL_META_EDITOR
; Pure resident admission; never enter bank code just to test its lifetime.
global _line_overlay_available
_line_overlay_available:
 xor ax,ax
 cmp word [cs:phase],0
 jne .done
 cmp word [cs:fatal],0
 jne .done
 cmp word [cs:busy],0
 jne .done
 inc ax
.done:retf
%endif
