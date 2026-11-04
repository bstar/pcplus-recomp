; Maintained foreground Auto Answer notice and generation-owned short tone.
; Full UI entry ABI preserves registers/FLAGS; admit returns AX0/1 only.
BITS 16
CPU 8086
%ifdef TERMINAL_AUTO_ANSWER
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global terminal_auto_answer_ui_code_start,terminal_auto_answer_ui_code_end
terminal_auto_answer_ui_code_start:
extern terminal_manual_init_active,terminal_manual_init_status
extern _terminal_sound_enabled
extern _speaker_start,_speaker_poll,_speaker_stop,_speaker_active,_speaker_generation
extern connection_notice_resident,connection_notice_restore_resident
extern text_video_segment,screen_columns,screen_last_row,screen_video_row_bytes
extern terminal_status_row_admit_far
%macro ui_save 0
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
%macro ui_restore 0
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

global terminal_auto_answer_admit_far
terminal_auto_answer_admit_far:
 push bx
 push es
 call far terminal_status_row_admit_far
 jc .bad
 mov ah,0x0f
 int 0x10
 cmp ah,80
 jne .bad
 cmp al,2
 je .mode
 cmp al,3
 jne .bad
.mode:
 or bh,bh
 jnz .bad
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x84],24
 jne .bad
 cmp word [text_video_segment],0xb800
 jne .bad
 cmp word [screen_columns],80
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [screen_last_row],23
 jne .bad
 xor ax,ax
 jmp .done
.bad:
 mov ax,1
.done:
 pop es
 pop bx
 retf

global terminal_auto_answer_ui_start_far,terminal_auto_answer_ui_poll_far,terminal_auto_answer_ui_stop_far
terminal_auto_answer_ui_start_far:
 ui_save
 call stop_body
 cmp word [_terminal_sound_enabled],0
 je .notice
 ; Maintained four BIOS ticks at440Hz, bounded and serviced, not native timing.
 mov ax,15
 push ax
 mov ax,0x4240
 push ax
 mov ax,4
 push ax
 mov ax,440
 push ax
 call _speaker_start
 add sp,8
 cmp ax,1
 jne .notice ; Busy/foreign hardware is never stolen.
 mov word [cs:sound_owned],1
 call _speaker_generation
 mov [cs:sound_generation],ax
.notice:
 mov si,auto_answer_message
 call far connection_notice_resident
 mov word [cs:terminal_auto_answer_notice_active],1
 ui_restore

terminal_auto_answer_ui_poll_far:
 ui_save
 cmp word [terminal_manual_init_active],0
 jne .sound
 cmp word [terminal_manual_init_status],2
 je .sent
 call stop_body
 jmp .done
.sent:
 call restore_notice
.sound:
 cmp word [cs:sound_owned],0
 je .done
 cmp word [_terminal_sound_enabled],0
 jne .ownership
 call stop_sound
 jmp .done
.ownership:
 call owns_sound
 or ax,ax
 jz .lost
 call _speaker_poll
 cmp ax,1
 je .done
.lost:
 mov word [cs:sound_owned],0
.done:
 ui_restore

terminal_auto_answer_ui_stop_far:
 ui_save
 call stop_body
 ui_restore

stop_body:
 call restore_notice
stop_sound:
 cmp word [cs:sound_owned],0
 je .done
 call owns_sound
 or ax,ax
 jz .clear
 call _speaker_stop
.clear:
 mov word [cs:sound_owned],0
.done:
 ret

owns_sound:
 call _speaker_active
 or ax,ax
 jz .done
 call _speaker_generation
 cmp ax,[cs:sound_generation]
 jne .no
 mov ax,1
 ret
.no:
 xor ax,ax
.done:
 ret

restore_notice:
 cmp word [cs:terminal_auto_answer_notice_active],0
 je .done
 call far connection_notice_restore_resident
 mov word [cs:terminal_auto_answer_notice_active],0
.done:
 ret

global terminal_auto_answer_notice_active
terminal_auto_answer_notice_active: dw 0
sound_owned: dw 0
sound_generation: dw 0
terminal_auto_answer_ui_code_end:
SEGMENT _DATA public class=DATA use16
auto_answer_message: db 'AUTO ANSWER...',0
%endif
