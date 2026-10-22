; One user-origin bit for each of the1024 queued bytes. Mutable loaded bank
; storage keeps this128-byte state outside DGROUP, retained with CONFIG_CODE.
; Every enqueue overwrites its bit; successful delivery clears it. Discarded
; slots cannot leak provenance when the ring wraps or resets.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern _recording_terminal_cookie,_recording_terminal_owner
extern _recording_terminal_transmit
global terminal_tx_origin_set_far,terminal_tx_origin_delivered_far
global terminal_record_user_delivered_far
global terminal_tx_origin_bits,terminal_tx_origin_bits_end
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
%endmacro
%macro restore 0
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
%endmacro
; BX=ring slot, DX=0(report/dedicated) or1(user/binding/paste).
; All registers and flags preserved; no IO and no callback.
terminal_tx_origin_set_far:
 save
 mov di,dx
 mov si,bx
 shr si,1
 shr si,1
 shr si,1
 mov cx,bx
 and cl,7
 mov dl,1
 shl dl,cl
 test di,1
 jz .clear
 or [cs:terminal_tx_origin_bits+si],dl
 jmp .done
.clear:
 not dl
 and [cs:terminal_tx_origin_bits+si],dl
.done:
 restore
; BX=accepted head slot, AL=byte actually accepted by uart_try_write.
; Never called on a busy/rejected write. Clear origin before any DOS callback.
terminal_tx_origin_delivered_far:
 save
 mov di,ax
 mov si,bx
 shr si,1
 shr si,1
 shr si,1
 mov cx,bx
 and cl,7
 mov dl,1
 shl dl,cl
 test [cs:terminal_tx_origin_bits+si],dl
 jz .done
 not dl
 and [cs:terminal_tx_origin_bits+si],dl
 call record_accepted_user
.done:
 restore
; TEXT bindings bypass the ring, but use the same post-acceptance recorder.
terminal_record_user_delivered_far:
 save
 mov di,ax
 call record_accepted_user
 restore
record_accepted_user:
 cmp word [_recording_terminal_cookie],0x5244
 jne .done
 cmp word [_recording_terminal_owner+136],1 ;offsetof(state), RF_RECORDING
 jne .done
 mov ax,di
 and ax,255
 push ax
 call far _recording_terminal_transmit
 add sp,2
.done:
 ret
terminal_tx_origin_bits: times 128 db 0
terminal_tx_origin_bits_end:
