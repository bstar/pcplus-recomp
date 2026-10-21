; Test-only BIOS keyboard helper for an unsaved editor draft. Wait for the
; KEYTEST subject and initial editor status, then inject real BIOS keys.
; No application state, serial bytes or terminal replies are injected.
bits 16
cpu 8086
org 100h
jmp install
old_vector: dd 0
state: db 0
; Bound failed prerequisites too: return via the product's actual Alt-X path
; before the outer720s watchdog. No editor/pass marker is synthesized.
%ifndef AUDIO_EDITOR_WATCHDOG_TICKS
%ifdef AUDIO_EDITOR_MULTILINE
%define AUDIO_EDITOR_WATCHDOG_TICKS 21600
%else
%define AUDIO_EDITOR_WATCHDOG_TICKS 12600
%endif
%endif
%ifdef AUDIO_EDITOR_MULTILINE
%ifdef AUDIO_EDITOR_BURST
%error "Choose multiline or single-line burst keys"
%endif
%define AUDIO_EDITOR_BURST 1
%endif
%ifndef AUDIO_EDITOR_KEY_TICKS
%define AUDIO_EDITOR_KEY_TICKS 54
%endif
%ifndef AUDIO_EDITOR_INITIAL_TICKS
%define AUDIO_EDITOR_INITIAL_TICKS 360
%endif
watchdog: dw AUDIO_EDITOR_WATCHDOG_TICKS
ticks: dw 0
key_at: dw keys
prompt: db 'KEYTEST',0
footer: db 'INS 01,01',0
%ifdef AUDIO_EDITOR_BURST
%ifdef AUDIO_EDITOR_MULTILINE
final_text: db 'TAIL',0
final_footer: db 'OVR 31,05',0
%else
final_text: db 'UNSAVED',0
final_footer: db 'OVR 01,08',0
%endif
%endif
%ifdef AUDIO_EDITOR_MULTILINE
keys:
%assign line 1
%rep 30
%assign tens line/10
%assign units line-(line/10)*10
 dw 264ch
%if tens == 0
 dw 0b30h
%else
 dw ((tens+1)<<8)+'0'+tens
%endif
%if units == 0
 dw 0b30h
%else
 dw ((units+1)<<8)+'0'+units
%endif
 dw 273ah,1e41h,3042h,2e43h,2044h
%if line < 30
 dw 1c0dh
%endif
%assign line line+1
%endrep
 dw 4800h,4700h,2348h,5300h,4f00h,5000h,0e08h,1c0dh
 dw 1454h,1e41h,1749h,264ch
 dw 4900h,4900h,4900h,5100h,5100h,5100h,5200h,2d00h,0
%else
keys: dw 1e41h,3042h,2e43h,2044h,1245h,4700h,2348h,4f00h,1245h
      dw 4b00h,5300h,5200h,2c5ah,0f09h,1454h,4900h,5100h,1519h
      dw 1655h,314eh,1f53h,1e41h,2f56h,1245h,2044h,2d00h,0
%endif
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
 cmp byte [state],2
 je .done
 dec word [watchdog]
 jnz .watching
 mov cx,2d00h
 mov ah,5
 int 16h
 or al,al
 jz .restore
 inc word [watchdog] ; BIOS queue full: retry without inventing success
 jmp .done
.watching:
%ifdef AUDIO_EDITOR_BURST
 cmp byte [state],3
 je .final_screen
%endif
 cmp byte [state],0
 jne .count
 mov si,prompt
 call visible
 jnc .done
 mov si,footer
 call visible
 jnc .done
 mov byte [state],1
 mov word [ticks],AUDIO_EDITOR_INITIAL_TICKS ; default: 20 seconds for header/body completion and child return
 jmp .done
.count:
 cmp byte [state],1
 jne .done
 dec word [ticks]
 jnz .done
 mov bx,[key_at]
 mov cx,[bx]
 mov ah,5
 int 16h
 or al,al
 jz .accepted
 inc word [ticks]
 jmp .done
.accepted:
 add word [key_at],2
 mov bx,[key_at]
 cmp word [bx],0
 je .restore
 mov word [ticks],AUDIO_EDITOR_KEY_TICKS ; default: three seconds between keys
 cmp word [bx],2d00h
 jne .done
%ifdef AUDIO_EDITOR_BURST
 mov byte [state],3 ; wait for actual final text/cursor, not a fixed send delay
%else
 mov word [ticks],180 ; drain the final editor response before Alt-X
%endif
 jmp .done
%ifdef AUDIO_EDITOR_BURST
.final_screen:
 mov si,final_text
 call visible
 jnc .done
 mov si,final_footer
 call visible
 jnc .done
 mov byte [state],1
 mov word [ticks],36 ; drain the remainder of the final response before Alt-X
 jmp .done
%endif
.restore:
 mov byte [state],2
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
; Scan visible CP437 character cells only. CF1 means found; registers other
; than AX/DI/ES are preserved so two independent markers can be required.
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
 cmp al,[es:di]
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
