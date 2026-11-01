; Owned DOS fixture: delay first real log data write with IRQs enabled.
; Reads parent UART counters through its actual DS; never writes product state.
BITS 16
CPU 8086
ORG 100h
%ifndef DELAY_TICKS
%define DELAY_TICKS 9
%endif
%ifdef WATERMARK
%define SAMPLE_BYTES 48
%elifdef CARRIER
%define SAMPLE_BYTES 52
%else
%define SAMPLE_BYTES 32
%endif
%ifndef MCR_PORT
%define MCR_PORT 3fch
%endif
jmp start
old_dos: dd 0
%ifdef WATERMARK
old_timer: dd 0
resident_segment: dw 0
%endif
sample: dw 0x534c,0,DELAY_TICKS,0,0,0,0,0,0,0,0,0,0xffff,0,0,0
%ifdef WATERMARK
 dw 0,0,0,0,0,0,0,0
%define PENDING_SEEN (sample+32)
%define XOFF_SEEN (sample+34)
%define RTS_SEEN (sample+36)
%define POST_SAMPLES (sample+38)
%define BAD_RTS (sample+40)
%define POST_PENDING (sample+42)
%define DRIVER_RELEASED (sample+44)
%define ENTRY_EPOCH (sample+46)
%endif
%ifdef CARRIER
 dw 0,0,0,0
 times 6 dw 0
%define ENTRY_MSR (sample+32)
%define LAST_MSR (sample+34)
%define LOST_DURING_HOLD (sample+36)
%define HIGH_DURING_HOLD (sample+38)
%define ORIGINAL_STAMP (sample+40)
%endif
%define FIRED (sample+2)
%define ELAPSED (sample+6)
%define ENTRY_FLAGS (sample+8)
%define ACTIVE (sample+10)
%define RX_BEFORE (sample+12)
%define RX_PEAK (sample+14)
%define DROP_BEFORE (sample+16)
%define DROP_AFTER (sample+18)
%define REAL_AX (sample+20)
%define REAL_FLAGS (sample+22)
%define HELD (sample+24)
%define MCR (sample+26)
%define WAIT_FLAGS (sample+28)
%define PARENT_DS (sample+30)
path: db 'D:\PCPLUS.FON',0
handler:
 pushf
 push bp
 mov bp,sp
 cmp word [cs:FIRED],0
 jne .pass
 cmp ah,3ch
 je .open
 cmp ah,3dh
 je .open
 cmp ah,5bh
 je .open
 cmp ah,40h
 jne .pass
 cmp bx,[cs:HELD]
 jne .pass
 or cx,cx
 jz .pass
 mov word [cs:FIRED],1
 mov ax,[ss:bp+8]
 mov [cs:ENTRY_FLAGS],ax
 call hold
 ; Restore the genuine data-write function; AX was used to read FLAGS.
 mov ah,40h
 pushf
 call far [cs:old_dos]
 mov [cs:REAL_AX],ax
 pushf
 pop word [cs:REAL_FLAGS]
 jc .error
 and word [ss:bp+8],0xfffe
 jmp .return
.open:
 call matches
 jnc .pass
 pushf
 call far [cs:old_dos]
 jc .error
 mov [cs:HELD],ax
 and word [ss:bp+8],0xfffe
 jmp .return
.error:
 or word [ss:bp+8],1
.return:
 pop bp
 popf
 iret
.pass:
 pop bp
 popf
 jmp far [cs:old_dos]
hold:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push es
 mov ax,ds
 mov [cs:PARENT_DS],ax
%ifdef WATERMARK
 mov ax,[EVENT_EPOCH_OFFSET]
 mov [cs:ENTRY_EPOCH],ax
%endif
 xor ax,ax
 mov al,[HARDWARE_ACTIVE_OFFSET]
 mov [cs:ACTIVE],ax
 mov ax,[RX_COUNT_OFFSET]
 mov [cs:RX_BEFORE],ax
 mov [cs:RX_PEAK],ax
 mov ax,[RX_DROPPED_OFFSET]
 mov [cs:DROP_BEFORE],ax
 mov dx,MCR_PORT
 in al,dx
 xor ah,ah
 mov [cs:MCR],ax
%ifdef CARRIER
 mov dx,[MSR_PORT_OFFSET]
 in al,dx
 xor ah,ah
 mov [cs:ENTRY_MSR],ax
%assign stamp_word 0
%rep 6
 mov ax,[LIFECYCLE_OFFSET+14+stamp_word*2]
 mov [cs:ORIGINAL_STAMP+stamp_word*2],ax
%assign stamp_word stamp_word+1
%endrep
%endif
 test word [cs:ENTRY_FLAGS],200h
 jz .done
 mov ax,40h
 mov es,ax
 mov si,[es:6ch]
 mov cx,0xffff
 mov bx,64
 sti
.loop:
 mov ax,[RX_COUNT_OFFSET]
 cmp ax,[cs:RX_PEAK]
 jbe .tick
 mov [cs:RX_PEAK],ax
.tick:
%ifdef WATERMARK
 call read_driver
%endif
%ifdef CARRIER
 mov dx,[MSR_PORT_OFFSET]
 in al,dx
 xor ah,ah
 mov [cs:LAST_MSR],ax
 test al,80h
 jnz .carrier_high
 mov word [cs:LOST_DURING_HOLD],1
 jmp .carrier_done
.carrier_high:
 mov word [cs:HIGH_DURING_HOLD],1
.carrier_done:
%endif
 pushf
 pop ax
 mov [cs:WAIT_FLAGS],ax
 mov ax,[es:6ch]
 sub ax,si
 cmp ax,DELAY_TICKS
 jae .elapsed
 loop .loop
 dec bx
 jz .elapsed
 mov cx,0xffff
 jmp .loop
.elapsed:
 mov [cs:ELAPSED],ax
 cli
.done:
 mov ax,[RX_DROPPED_OFFSET]
 mov [cs:DROP_AFTER],ax
 pop es
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
%ifdef WATERMARK
read_driver:
 xor ax,ax
 mov al,[FLOW_PENDING_OFFSET]
 or [cs:PENDING_SEEN],ax
 mov al,[XOFF_SENT_OFFSET]
 or [cs:XOFF_SEEN],ax
 mov al,[RTS_LOWERED_OFFSET]
 or [cs:RTS_SEEN],ax
 ret
timer_handler:
 pushf
 push ax
 push bx
 push dx
 push es
 cmp word [cs:FIRED],1
 jne .done
 cmp word [cs:REAL_AX],64
 jne .done
 xor ax,ax
 mov es,ax
 cmp word [es:12*4],ISR_OFFSET
 jne .done
 mov ax,[cs:PARENT_DS]
 sub ax,DATA_SEGMENT
 add ax,ISR_SEGMENT
 cmp ax,[es:12*4+2]
 jne .done
 mov ax,[cs:PARENT_DS]
 mov es,ax
 cmp byte [es:HARDWARE_ACTIVE_OFFSET],1
 jne .done
 mov ax,[es:EVENT_EPOCH_OFFSET]
 cmp ax,[cs:ENTRY_EPOCH]
 je .done
 xor bx,bx
 mov bl,[es:FLOW_PENDING_OFFSET]
 or [cs:POST_PENDING],bx
 cmp word [es:RX_COUNT_OFFSET],128
 jbe .released
 mov bl,[es:XOFF_SENT_OFFSET]
 or bl,[es:RTS_LOWERED_OFFSET]
 jz .done
 inc word [cs:POST_SAMPLES]
 cmp byte [es:RTS_LOWERED_OFFSET],1
 jne .done
 mov dx,3fch
 in al,dx
 test al,2
 jz .done
 inc word [cs:BAD_RTS]
 jmp .done
.released:
 cmp byte [es:XOFF_SENT_OFFSET],0
 jne .done
 cmp byte [es:RTS_LOWERED_OFFSET],0
 jne .done
 mov word [cs:DRIVER_RELEASED],1
.done:
 pop es
 pop dx
 pop bx
 pop ax
 popf
 jmp far [cs:old_timer]
%endif
matches:
 push ax
 push bx
 push cx
 push si
 mov si,dx
 add si,14
 jc .missing
 mov si,dx
 mov bx,path
 mov cx,14
.loop:
 mov al,[si]
 cmp al,[cs:bx]
 jne .missing
 inc si
 inc bx
 loop .loop
 pop si
 pop cx
 pop bx
 pop ax
 stc
 ret
.missing:
 pop si
 pop cx
 pop bx
 pop ax
 clc
 ret
resident_end:
start:
 mov ax,3521h
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_dos],bx
 mov [old_dos+2],es
%ifdef WATERMARK
 mov ax,351ch
 int 21h
 mov [old_timer],bx
 mov [old_timer+2],es
 mov dx,timer_handler
 mov ax,251ch
 int 21h
%endif
 mov dx,handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x534c
 jne failed
%ifdef WATERMARK
 mov ax,es
 mov [resident_segment],ax
%endif
 mov si,sample
 mov di,buffer
 mov cx,SAMPLE_BYTES
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
%ifdef WATERMARK
 mov ax,[es:old_timer]
 mov [old_timer],ax
 mov ax,[es:old_timer+2]
 mov [old_timer+2],ax
%endif
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 mov [old_dos],dx
 mov [old_dos+2],ax
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[old_dos]
 jne failed
 mov ax,es
 cmp ax,[old_dos+2]
 jne failed
%ifdef WATERMARK
 mov ax,351ch
 int 21h
 cmp bx,timer_handler
 jne failed
 ; The timer must still belong to the same resident owner as INT21 did.
 mov ax,es
 cmp ax,[resident_segment]
 jne failed
 cmp word [es:sample],0x534c
 jne failed
 push ds
 mov dx,[old_timer]
 mov ds,[old_timer+2]
 mov ax,251ch
 int 21h
 pop ds
 mov ax,351ch
 int 21h
 cmp bx,[old_timer]
 jne failed
 mov ax,es
 cmp ax,[old_timer+2]
 jne failed
%endif
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,SAMPLE_BYTES
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,SAMPLE_BYTES
 jne .close_failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
.close_failed:
 mov ah,3eh
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\SLOW.BIN',0
buffer: times SAMPLE_BYTES db 0
