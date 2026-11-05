; Test-only BIOS keyboard helper for an unsaved editor draft. Wait for the
; KEYTEST subject and Synchronet Insert Mode status, then inject real BIOS keys.
; No application state, serial bytes or terminal replies are injected.
; Final Alt-X waits for the rendered Main menu AND its footer, then drains.
bits 16
cpu 8086
org 100h
jmp install
%ifndef AUDIO_SYNC_EDITOR_SETTLE
%define AUDIO_SYNC_EDITOR_SETTLE 360
%endif
%ifndef AUDIO_SYNC_EDITOR_KEY_WAIT
%define AUDIO_SYNC_EDITOR_KEY_WAIT 54
%endif
%ifndef AUDIO_SYNC_EDITOR_FINAL_WAIT
%define AUDIO_SYNC_EDITOR_FINAL_WAIT 180
%endif
; Explicit owned-layout variant; the default retains its original25-row bytes.
%ifndef AUDIO_SYNC_EDITOR_SCREEN_BYTES
%define AUDIO_SYNC_EDITOR_SCREEN_BYTES 4000
%endif
%if AUDIO_SYNC_EDITOR_SCREEN_BYTES != 4000 && AUDIO_SYNC_EDITOR_SCREEN_BYTES != 4480 && AUDIO_SYNC_EDITOR_SCREEN_BYTES != 6880 && AUDIO_SYNC_EDITOR_SCREEN_BYTES != 8000
%error Unsupported owned text-screen extent
%endif
old_vector: dd 0
state: db 0
; Bound failed prerequisites too: return via the product's actual Alt-X path
; before the outer950s watchdog. No editor/pass marker is synthesized.
%ifndef AUDIO_SYNC_EDITOR_WATCHDOG_TICKS
%define AUDIO_SYNC_EDITOR_WATCHDOG_TICKS 16200
%endif
watchdog: dw AUDIO_SYNC_EDITOR_WATCHDOG_TICKS
ticks: dw 0
key_at: dw keys
prompt: db 'KEYTEST',0
%ifdef ENIGMA_MULTILINE
footer: db 'INS 01,01',0
%else
footer: db 'Insert Mode',0
%endif
main_prompt: db 'Read/Post Messages',0
main_footer: db 'Local [',0
%ifdef ENIGMA_MULTILINE
keys:
%include "multiline_keys.inc"
%else
keys:
%ifdef FILE_VIEWER_ROUNDTRIP
 dw 2f00h,2044h,273ah,2b5ch,2f56h,1749h,1245h,1157h,342eh,2044h,1e41h,1454h,1c0dh,011bh
%endif
%ifdef FILE_DIRECTORY_ROUNDTRIP
 dw 2100h,2044h,273ah,2b5ch,1454h,1245h,1f53h,1454h,342eh,1950h,1352h,324dh,1c0dh,011bh
%endif
%ifdef GATEWAY_ROUNDTRIP
 dw 6b00h
%endif
 dw 1519h,1e41h,3042h,2e43h,2044h,1245h,4700h,2348h,4f00h,1245h
      dw 4b00h,5300h,5200h,2c5ah,0f09h,1454h,4900h,5100h,1519h
      dw 1655h,314eh,1f53h,1e41h,2f56h,1245h,2044h,1011h,3920h,2d00h,0
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
 cmp byte [state],0
 jne .count
 mov si,prompt
 call visible
 jnc .done
 mov si,footer
 call visible
 jnc .done
 mov byte [state],1
 mov word [ticks],AUDIO_SYNC_EDITOR_SETTLE
 jmp .done
.count:
 cmp byte [state],1
 jne .done
 mov bx,[key_at]
 cmp word [bx],2d00h
 jne .tick
%ifndef SCREEN_REFERENCE_FREEZE
 ; The editor/abort clears old Main text. Neither a partial menu nor an
 ; elapsed fixed delay proves its final3500-byte screen has arrived.
 mov si,main_prompt
 call visible
 jnc .done
 mov si,main_footer
 call visible
 jnc .done
%endif
.tick:
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
 mov word [ticks],AUDIO_SYNC_EDITOR_KEY_WAIT
%ifdef FILE_DIRECTORY_ROUNDTRIP
 cmp word [bx-2],2100h
 jne .listing_enter
 mov word [ticks],18
.listing_enter:
 cmp word [bx-2],1c0dh
 jne .listing_escape
 mov word [ticks],36
.listing_escape:
 cmp word [bx-2],011bh
 jne .listing_wait_done
 mov word [ticks],18
.listing_wait_done:
%endif
%ifdef FILE_VIEWER_ROUNDTRIP
 cmp word [bx-2],2f00h
 jne .viewer_enter
 mov word [ticks],18
.viewer_enter:
 cmp word [bx-2],1c0dh
 jne .viewer_escape
 mov word [ticks],36
.viewer_escape:
 cmp word [bx-2],011bh
 jne .viewer_wait_done
 mov word [ticks],18
.viewer_wait_done:
%endif
%ifdef GATEWAY_ROUNDTRIP
 cmp word [bx-2],6b00h
 jne .ordinary_wait
 mov word [ticks],72 ; Real graphics child and automatic foreground restore.
.ordinary_wait:
%endif
 cmp word [bx],2d00h
 jne .done
 mov word [ticks],AUDIO_SYNC_EDITOR_FINAL_WAIT
 jmp .done
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
 cmp di,AUDIO_SYNC_EDITOR_SCREEN_BYTES
 jae .miss
 cmp al,[es:di]
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,AUDIO_SYNC_EDITOR_SCREEN_BYTES
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
