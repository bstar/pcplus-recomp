; Maintained read-only native DOS directory chooser; no UART access or writes.
; AX=0 selected /1 cancel /2 file or unsupported-video error.
; DS=SS,DF=0; BP/SI/DI/ES preserved. Stages selection until Enter.
; Actual page reader provides raw114-byte records. Only bounded name24 and
; number20 fields are rendered; password/script/KEY/META are never displayed.
BITS 16
CPU 8086
%include "trap_wait.inc"
%include "directory_dos.inc"
SEGMENT _TEXT public class=CODE use16
extern _directory_dos_page
extern terminal_directory_path,terminal_directory_entry,terminal_directory_codes
extern terminal_screen_save_far,terminal_screen_restore_far,text_video_segment
extern terminal_directory_edit_selected
global terminal_directory_choose
terminal_directory_choose:
 push bp
 push si
 push di
 push es
 cld
%ifdef TERMINAL_NATIVE_RESET_OVERLAY
 extern terminal_program_pending,terminal_program_active,_redisplay_active,terminal_editor_screen_owned
 cmp byte [browser_saved],0
 jne .busy
 cmp word [terminal_program_pending],0
 jne .busy
 cmp word [terminal_program_active],0
 jne .busy
 cmp word [_redisplay_active],0
 jne .busy
 cmp byte [terminal_editor_screen_owned],0
 jne .busy
%endif
 mov word [browser_result],2
 mov word [browser_notice],0
 mov byte [browser_saved],0
 mov ah,0x0f
 call browser_bios
 cmp ah,80
 jne .finish
 cmp al,2
 je .color
 cmp al,3
 je .color
 cmp al,7
 jne .finish
 mov ax,0xb000
 jmp .video
.color:
 mov ax,0xb800
.video:
 mov [browser_page],bh
 mov dx,[text_video_segment]
 mov [browser_old_segment],dx
 mov [text_video_segment],ax
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x4e]
 cmp ax,61536
 ja .restore_segment
 mov [browser_video_offset],ax
 mov ah,3
 mov bh,[browser_page]
 call browser_bios
 mov [browser_cursor],dx
 mov [browser_shape],cx
 mov ax,[browser_screen_segment]
 mov es,ax
 mov di,browser_screen
 mov dx,[browser_video_offset]
 mov ax,2000
 call terminal_screen_save_far
 jc .restore_segment
 mov byte [browser_saved],1
 mov word [browser_selected],0
 mov ax,[terminal_directory_entry]
 or ax,ax
 jz .initial
 cmp ax,200
 ja .initial
 dec ax
 mov [browser_selected],ax
.initial:
 mov word [browser_first],0
.refresh:
 mov ax,[browser_selected]
 xor dx,dx
 mov bx,10
 div bx
 mul bx
 inc ax
 cmp ax,[browser_first]
 je .paint
 mov [browser_first],ax
 push ds
 pop es
 mov dx,browser_io
 push dx
 mov dx,browser_page_data
 push dx
 push ax
 mov dx,terminal_directory_path
 push dx
 call _directory_dos_page
 add sp,8
 or ax,ax
 jnz .restore
 mov ax,[browser_page_data+DD_PAGE_FIRST]
 cmp ax,[browser_first]
 jne .restore
 cmp word [browser_page_data+DD_PAGE_COUNT],10
 jne .restore
.paint:
 call browser_paint
.key:
 TERMINAL_WAIT_KEY ah
 cmp al,27
 je .cancel
 cmp al,13
 je .select
 cmp al,'e'
 je .edit
 cmp al,'E'
 je .edit
 cmp ah,0x48
 je .up
 cmp ah,0x50
 je .down
 cmp ah,0x49
 je .page_up
 cmp ah,0x51
 je .page_down
 cmp ah,0x47
 je .home
 cmp ah,0x4f
 je .end
 jmp .key
.edit:
 mov ax,[browser_selected]
 inc ax
 sub ax,[browser_first]
 mov bx,114
 mul bx
 add ax,browser_page_data+DD_PAGE_RECORDS
 push ax
 mov ax,[browser_selected]
 inc ax
 push ax
 call terminal_directory_edit_selected
 add sp,4
 mov [browser_notice],ax
 or ax,ax
 jz .paint
 cmp ax,2
 je .paint
 mov word [browser_first],0
 jmp .refresh
.up:
 cmp word [browser_selected],0
 je .key
 dec word [browser_selected]
 jmp .refresh
.down:
 cmp word [browser_selected],199
 je .key
 inc word [browser_selected]
 jmp .refresh
.page_up:
 mov ax,[browser_selected]
 sub ax,10
 jnc .move
 xor ax,ax
 jmp .move
.page_down:
 mov ax,[browser_selected]
 add ax,10
 cmp ax,199
 jbe .move
 mov ax,199
 jmp .move
.home:
 xor ax,ax
 jmp .move
.end:
 mov ax,199
.move:
 mov [browser_selected],ax
 jmp .refresh
.select:
 mov ax,[browser_selected]
 inc ax
 mov [terminal_directory_entry],ax
 mov word [browser_result],0
 jmp .restore
.cancel:
 mov word [browser_result],1
.restore:
 cmp byte [browser_saved],0
 je .restore_segment
 mov ax,[browser_screen_segment]
 mov es,ax
 mov si,browser_screen
 mov dx,[browser_video_offset]
 mov ax,2000
 call terminal_screen_restore_far
 mov cx,[browser_shape]
 mov ah,1
 call browser_bios
 mov dx,[browser_cursor]
 mov bh,[browser_page]
 mov ah,2
 call browser_bios
.restore_segment:
 mov ax,[browser_old_segment]
 mov [text_video_segment],ax
.finish:
%ifdef TERMINAL_NATIVE_RESET_OVERLAY
 mov byte [browser_saved],0
%endif
 mov ax,[browser_result]
.unwind:
 pop es
 pop di
 pop si
 pop bp
 ret

%ifdef TERMINAL_NATIVE_RESET_OVERLAY
.busy:
 mov ax,2
 jmp .unwind
%endif

; Guard against historical INT10 implementations clobbering BP/DS/ES.
browser_bios:
 push bp
 push si
 push di
 push ds
 push es
 int 0x10
 pop es
 pop ds
 pop di
 pop si
 pop bp
 ret

browser_paint:
 mov ax,0x0600
 mov bh,7
 xor cx,cx
 mov dx,0x184f
 call browser_bios
 mov byte [browser_attribute],7
 mov word [browser_position],0x0102
 mov si,browser_title
 call browser_string
 mov word [browser_position],0x0302
 mov si,browser_columns
 call browser_string
 mov si,browser_page_data+DD_PAGE_RECORDS
 xor di,di
.row:
 mov ax,di
 add al,5
 mov ah,al
 mov al,2
 mov [browser_position],ax
 mov ax,[browser_first]
 add ax,di
 mov byte [browser_attribute],7
 dec ax
 cmp ax,[browser_selected]
 jne .ordinary
 mov byte [browser_attribute],0x70
.ordinary:
 inc ax
 call browser_decimal
 mov byte [browser_position],8
 mov cx,24
 call browser_field
 mov byte [browser_position],35
 add si,DD_REC_NUMBER
 mov cx,20
 call browser_field
 add si,DD_RECORD_SIZE-DD_REC_NUMBER
 inc di
 cmp di,10
 jb .row
 mov byte [browser_attribute],7
 mov word [browser_position],0x1602
 mov si,browser_keys
 call browser_string
 mov word [browser_position],0x1702
 mov si,browser_literal
 cmp word [terminal_directory_codes],0
 je .mode
 mov si,browser_legacy
.mode:
 call browser_string
 mov word [browser_position],0x1402
 mov si,browser_no_notice
 cmp word [browser_notice],0
 je .notice
 mov si,browser_saved_notice
 cmp word [browser_notice],1
 je .notice
 mov si,browser_error_notice
 cmp word [browser_notice],2
 je .notice
 mov si,browser_warning_notice
.notice:
 call browser_string
 ret
; Field SI,CX is raw storage: bounded scan, NUL pads remainder, controls sanitize.
; SI remains unchanged so row stepping cannot drift into password fields.
browser_field:
 push si
 push bx
 xor bx,bx
.next:
 mov al,[si]
 inc si
 or al,al
 jz .padding
 or bx,bx
 jnz .padding
 cmp al,32
 jb .sanitize
 cmp al,127
 jne .put
.sanitize:
 mov al,'.'
 jmp .put
.padding:
 mov bx,1
 mov al,' '
.put:
 call browser_character
 loop .next
 pop bx
 pop si
 ret
browser_string:
 lodsb
 or al,al
 jz .done
 call browser_character
 jmp browser_string
.done:
 ret
browser_decimal:
 push si
 mov si,browser_digits+3
 mov byte [si],0
 mov bx,10
.digit:
 xor dx,dx
 div bx
 add dl,'0'
 dec si
 mov [si],dl
 or ax,ax
 jnz .digit
 call browser_string
 pop si
 ret
browser_character:
 push ax
 push bx
 push cx
 push dx
 mov [browser_character_value],al
 mov dx,[browser_position]
 mov bh,[browser_page]
 mov ah,2
 call browser_bios
 mov al,[browser_character_value]
 mov ah,9
 mov bh,[browser_page]
 mov bl,[browser_attribute]
 mov cx,1
 call browser_bios
 inc byte [browser_position]
 pop dx
 pop cx
 pop bx
 pop ax
 ret

SEGMENT _DATA public class=DATA use16
browser_result: dw 2
browser_notice: dw 0
global terminal_browser_screen_owned
terminal_browser_screen_owned:
browser_saved: db 0
browser_page: db 0
browser_old_segment: dw 0
browser_video_offset: dw 0
browser_cursor: dw 0
browser_shape: dw 0
browser_selected: dw 0
browser_first: dw 0
browser_position: dw 0
browser_attribute: db 7
browser_character_value: db 0
browser_digits: times 4 db 0
browser_title: db 'PCPLUS // DIRECTORY',0
browser_columns: db 'ENTRY NAME                       NUMBER',0
browser_keys: db 'Up/Down PgUp/PgDn Home/End  E edit  Enter select  Esc cancel',0
browser_literal: db 'LITERAL targets // E edits selected entry // 200 entries',0
browser_legacy: db 'LEGACY A..J codes // E edits selected entry // 200 entries',0
browser_no_notice: db 0
browser_saved_notice: db 'Entry saved.',0
browser_error_notice: db 'Save failed. Check directory and recovery files.',0
browser_warning_notice: db 'Entry installed; recovery files retained. Check before another save.',0
browser_io: times DD_RESULT_SIZE db 0
browser_page_data: times DD_PAGE_SIZE db 0
global browser_screen_segment
browser_screen_segment: dw seg browser_screen
SEGMENT UI_STORAGE public align=16 class=FAR_DATA use16
GROUP UI_GROUP UI_STORAGE
global browser_screen,browser_screen_end
browser_screen: resb 4000
browser_screen_end:

%ifdef TERMINAL_NATIVE_RESET_OVERLAY
; The synchronous chooser restores before any queued PROGRAM can launch.
; Bidirectional admission prevents this shared backup from changing owners
; until the old owner has restored its display.
global program_screen,program_screen_end
program_screen equ browser_screen
program_screen_end equ browser_screen_end
%endif
