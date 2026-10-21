; Test-only BIOS exit after actual file/message/fresh-main phases; no product
; state, DOS-in-timer calls, UART access or fabricated server replies.
bits 16
cpu 8086
org 100h
jmp install
%ifndef AUDIO_SYNCHRONET_WATCHDOG
%define AUDIO_SYNCHRONET_WATCHDOG 16200
%endif
%ifndef AUDIO_SYNCHRONET_FINAL_WAIT
%define AUDIO_SYNCHRONET_FINAL_WAIT 180
%endif
old_vector: dd 0
state: db 0
ticks: dw 0
watchdog: dw AUDIO_SYNCHRONET_WATCHDOG
file_prompt: db 'List Files in dir',0
message_prompt: db 'No messages have been posted on ',0
main_prompt: db 'Read/Post Messages',0
main_footer: db 'Local [',0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 cld
 cmp byte [state],4
 je .done
 dec word [watchdog]
 jz .exit
 cmp byte [state],3
 je .count
 cmp byte [state],0
 jne .message
 mov si,file_prompt
 call visible
 jnc .done
 mov byte [state],1
 jmp .done
.message:
 cmp byte [state],1
 jne .main
 mov si,message_prompt
 call visible
 jnc .done
 mov byte [state],2
 jmp .done
.main:
 ; Old main text may remain behind the message pause. Require that pause
 ; text to disappear before recognizing the fresh final main screen.
 mov si,message_prompt
 call visible
 jc .done
 mov si,main_prompt
 call visible
 jnc .done
 mov si,main_footer
 call visible
 jnc .done
 mov byte [state],3
 mov word [ticks],AUDIO_SYNCHRONET_FINAL_WAIT
 jmp .done
.count:
 dec word [ticks]
 jnz .done
.exit:
 mov cx,2d00h
 mov ah,5
 int 16h
 or al,al
 jz .restore
 mov word [ticks],1
 mov word [watchdog],1
 jmp .done
.restore:
 mov byte [state],4
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[old_vector]
 mov [es:70h],ax
 mov ax,[old_vector+2]
 mov [es:72h],ax
 popf
.done:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
visible:
 push si
 mov ax,0b800h
 mov es,ax
 xor di,di
.search:
 pop si
 push si
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp di,4000
 jae .miss
 or al,20h
 mov ah,[es:di]
 or ah,20h
 cmp al,ah
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,4000
 jb .search
 pop si
 clc
 ret
.found:
 pop di
 pop si
 stc
 ret
resident_end:
filename: db 'D:\KEYOLD.BIN',0
install:
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ah,3ch
 xor cx,cx
 mov dx,filename
 int 21h
 jc failure
 mov bx,ax
 mov ah,40h
 mov cx,4
 mov dx,old_vector
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc failure
 cmp ax,4
 jne failure
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
failure:
 mov ax,4c01h
 int 21h
