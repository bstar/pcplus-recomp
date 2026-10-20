; Maintained read-only-until-accept DOS record editor, not original PCPlus UI.
; Near cdecl terminal_directory_edit(record_offset); caller removes2.
; AX0cancel/unsupportedvideo/invalidpointer, AX1accept. DS=SS,DF0.
; BP/SI/DI/ES preserved. No DOS/file/UART IO. Entire114byte stage commits onlyF10.
; Opaque tails/date/calls untouched. Password renders mask only. Storage enums
; intentionally exceed currently supported live terminal behavior.
BITS 16
CPU 8086
%include "directory_dos.inc"
%include "trap_wait.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_screen_save_far,terminal_screen_restore_far,text_video_segment
global terminal_directory_edit
terminal_directory_edit:
 push bp
 mov bp,sp
 push si
 push di
 push es
 cld
 mov word [ed_result],0
 mov byte [ed_saved],0
 mov si,[bp+4]
 mov ax,si
 add ax,DD_RECORD_SIZE
 jc .done
 mov [ed_record],si
 push ds
 pop es
 mov di,ed_stage
 mov cx,DD_RECORD_SIZE
 rep movsb
 mov ah,15
 call ed_bios
 cmp ah,80
 jne .done
 cmp al,2
 je .color
 cmp al,3
 je .color
 cmp al,7
 jne .done
 mov ax,0xb000
 jmp .video
.color:
 mov ax,0xb800
.video:
 mov [ed_page],bh
 mov dx,[text_video_segment]
 mov [ed_old_segment],dx
 mov [text_video_segment],ax
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x4e]
 cmp ax,61536
 ja .restore_segment
 mov [ed_video_offset],ax
 mov ah,3
 mov bh,[ed_page]
 call ed_bios
 mov [ed_old_cursor],dx
 mov [ed_old_shape],cx
 mov ax,[ed_screen_segment]
 mov es,ax
 mov di,ed_screen
 mov dx,[ed_video_offset]
 mov ax,2000
 call terminal_screen_save_far
 jc .restore_segment
 mov byte [ed_saved],1
 mov word [ed_field],0
 mov byte [ed_insert],0
 mov byte [ed_error],0
 call ed_focus
.redraw:
 call ed_paint
.key:
 TERMINAL_WAIT_KEY ah
 cmp al,27
 je .restore
 cmp al,9
 je .next
 cmp al,13
 je .next
 cmp al,8
 je .backspace
 or al,al
 jz .scan
 cmp al,0xe0
 jne .text
 or ah,ah
 jnz .scan
.text:
 cmp al,32
 jb .key
 cmp al,127
 je .key
 call ed_type
 jmp .redraw
.scan:
 cmp ah,0x44
 je .accept
 cmp ah,0x0f
 je .previous
 cmp ah,0x48
 je .previous
 cmp ah,0x50
 je .next
 cmp ah,0x4b
 je .left
 cmp ah,0x4d
 je .right
 cmp ah,0x47
 je .home
 cmp ah,0x4f
 je .end
 cmp ah,0x52
 je .insert
 cmp ah,0x53
 je .delete
 jmp .key
.left:
 cmp word [ed_cursor],0
 je .key
 dec word [ed_cursor]
 jmp .redraw
.right:
 mov ax,[ed_cursor]
 cmp ax,[ed_length]
 jae .key
 inc word [ed_cursor]
 jmp .redraw
.home:
 mov word [ed_cursor],0
 jmp .redraw
.end:
 mov ax,[ed_length]
 mov [ed_cursor],ax
 jmp .redraw
.insert:
 xor byte [ed_insert],1
 jmp .redraw
.backspace:
 cmp word [ed_cursor],0
 je .key
 dec word [ed_cursor]
.delete:
 call ed_delete
 jmp .redraw
.previous:
 call ed_commit_field
 jc .redraw
 cmp word [ed_field],0
 jne .prev_dec
 mov word [ed_field],16
.prev_dec:
 dec word [ed_field]
 call ed_focus
 jmp .redraw
.next:
 call ed_commit_field
 jc .redraw
 inc word [ed_field]
 cmp word [ed_field],16
 jb .new_focus
 mov word [ed_field],0
.new_focus:
 call ed_focus
 jmp .redraw
.accept:
 call ed_commit_field
 jc .redraw
 call ed_validate
 jc .redraw
 call ed_preserve_tails
 push ds
 pop es
 mov si,ed_stage
 mov di,[ed_record]
 mov cx,DD_RECORD_SIZE
 rep movsb
 mov word [ed_result],1
.restore:
 cmp byte [ed_saved],0
 je .restore_segment
 mov ax,[ed_screen_segment]
 mov es,ax
 mov si,ed_screen
 mov dx,[ed_video_offset]
 mov ax,2000
 call terminal_screen_restore_far
 mov cx,[ed_old_shape]
 mov ah,1
 call ed_bios
 mov dx,[ed_old_cursor]
 mov bh,[ed_page]
 mov ah,2
 call ed_bios
.restore_segment:
 mov ax,[ed_old_segment]
 mov [text_video_segment],ax
.done:
 mov ax,[ed_result]
 pop es
 pop di
 pop si
 pop bp
 ret

; BX=current8byte field descriptor; SI=stage field.
ed_descriptor:
 mov bx,[ed_field]
 shl bx,1
 shl bx,1
 shl bx,1
 add bx,ed_fields
 mov si,[bx]
 add si,ed_stage
 ret
; Text fields edit directly in private stage; numeric text is private scratch.
ed_focus:
 call ed_descriptor
 mov ax,[bx+2]
 and ax,255
 mov [ed_capacity],ax
 mov al,[bx+3]
 mov [ed_kind],al
 cmp al,1
 je .numeric
 cmp al,2
 je .numeric
 mov [ed_buffer],si
 jmp .length
.numeric:
 xor ax,ax
 mov al,[si]
 cmp byte [bx+3],2
 jne .format
 mov ax,[si]
.format:
 mov di,ed_number
 call ed_format
 mov word [ed_buffer],ed_number
.length:
 mov si,[ed_buffer]
 xor cx,cx
.scan:
 cmp cx,[ed_capacity]
 jae .ready
 cmp byte [si],0
 je .ready
 inc si
 inc cx
 jmp .scan
.ready:
 mov [ed_length],cx
 mov word [ed_cursor],0
 ret
; ReturnCF1 if currentnumeric input is empty/out-of-range. No stage update then.
ed_commit_field:
 call ed_descriptor
 cmp byte [ed_kind],1
 je .number
 cmp byte [ed_kind],2
 jne .good
.number:
 push si
 mov si,ed_number
 cmp byte [si],0
 je .bad_pop
 xor dx,dx
.digit:
 lodsb
 or al,al
 jz .range
 sub al,'0'
 cmp al,9
 ja .bad_pop
 xor ah,ah
 mov cx,ax
 mov ax,dx
 mov di,10
 mul di
 or dx,dx
 jnz .bad_pop
 add ax,cx
 jc .bad_pop
 mov dx,ax
 jmp .digit
.range:
 cmp dx,[bx+4]
 jb .bad_pop
 cmp dx,[bx+6]
 ja .bad_pop
 pop si
 mov [si],dl
 cmp byte [ed_kind],2
 jne .good
 mov [si],dx
.good:
 mov byte [ed_error],0
 clc
 ret
.bad_pop:
 pop si
 mov byte [ed_error],1
 stc
 ret
; All storage fields validate on F10. Existing opaque tails are never normalized.
ed_validate:
 mov cx,16
 mov bx,ed_fields
 xor di,di
.field:
 mov si,[bx]
 add si,ed_stage
 mov al,[bx+3]
 cmp al,1
 je .number
 cmp al,2
 je .number
 push cx
 xor cx,cx
 mov cl,[bx+2]
 inc cx
.text:
 lodsb
 or al,al
 jz .text_ok
 loop .text
 pop cx
 jmp .bad
.text_ok:
 pop cx
 jmp .next
.number:
 xor ax,ax
 mov al,[si]
 cmp byte [bx+3],2
 jne .range
 mov ax,[si]
.range:
 cmp ax,[bx+4]
 jb .bad
 cmp ax,[bx+6]
 ja .bad
.next:
 add bx,8
 inc di
 dec cx
 jnz .field
 clc
 ret
.bad:
 mov [ed_field],di
 call ed_focus
 mov byte [ed_error],1
 stc
 ret
 ; Restore every original text byte beyond the final NUL. Insert/delete may
; temporarily borrow opaque tail storage; acceptance preserves those tails.
ed_preserve_tails:
 mov bx,ed_fields
 mov dx,16
.field:
 cmp byte [bx+3],1
 je .next
 cmp byte [bx+3],2
 je .next
 mov si,[bx]
 mov di,si
 add si,ed_stage
 add di,[ed_record]
 xor cx,cx
 mov cl,[bx+2]
 inc cx
.scan:
 lodsb
 inc di
 dec cx
 or al,al
 jz .tail
 jcxz .next
 jmp .scan
.tail:
 jcxz .next
.copy:
 mov al,[di]
 mov [si],al
 inc si
 inc di
 loop .copy
.next:
 add bx,8
 dec dx
 jnz .field
 ret

; AL printable byte; insert/overwrite are bounded to declared visible capacity.
ed_type:
 cmp byte [ed_kind],1
 je .numeric
 cmp byte [ed_kind],2
 jne .allowed
.numeric:
 cmp al,'0'
 jb .done
 cmp al,'9'
 ja .done
.allowed:
 mov bx,[ed_cursor]
 mov si,[ed_buffer]
 add bx,si
 cmp byte [ed_insert],0
 je .overwrite
 mov dx,[ed_length]
 cmp dx,[ed_capacity]
 jae .done
 mov di,si
 add di,dx
 mov cx,dx
 sub cx,[ed_cursor]
 inc cx
.shift:
 mov ah,[di]
 mov [di+1],ah
 dec di
 loop .shift
 mov [bx],al
 inc word [ed_length]
 jmp .advance
.overwrite:
 mov dx,[ed_cursor]
 cmp dx,[ed_length]
 jb .replace
 cmp dx,[ed_capacity]
 jae .done
 mov byte [bx+1],0
 inc word [ed_length]
.replace:
 mov [bx],al
.advance:
 inc word [ed_cursor]
 mov byte [ed_error],0
.done:
 ret
ed_delete:
 mov cx,[ed_length]
 sub cx,[ed_cursor]
 jbe .done
 mov si,[ed_buffer]
 add si,[ed_cursor]
.shift:
 mov al,[si+1]
 mov [si],al
 inc si
 loop .shift
 dec word [ed_length]
 mov si,[ed_buffer]
 add si,[ed_length]
 mov byte [si],0
 mov byte [ed_error],0
.done:
 ret
; AX unsigned decimal -> NUL terminated DI; preserve surrounding field state.
ed_format:
 push bx
 push cx
 push dx
 push si
 push di
 mov si,ed_digits+5
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
.copy:
 lodsb
 mov [di],al
 inc di
 or al,al
 jnz .copy
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
ed_paint:
 mov ax,0x0600
 mov bh,0x17
 xor cx,cx
 mov dx,0x184f
 call ed_bios
 mov byte [ed_attribute],0x1f
 mov word [ed_position],0x0103
 mov si,ed_title
 call ed_string
 mov word [ed_position],0x0203
 mov si,ed_storage
 call ed_string
 mov word [ed_draw_index],0
.row:
 mov ax,[ed_draw_index]
 mov bx,ax
 shl bx,1
 add al,4
 mov ah,al
 mov al,3
 mov [ed_position],ax
 mov byte [ed_attribute],0x17
 mov si,[ed_labels+bx]
 call ed_string
 mov byte [ed_position],23
 mov bx,[ed_draw_index]
 cmp bx,[ed_field]
 jne .descriptor
 mov byte [ed_attribute],0x70
.descriptor:
 shl bx,1
 shl bx,1
 shl bx,1
 add bx,ed_fields
 mov si,[bx]
 add si,ed_stage
 xor cx,cx
 mov cl,[bx+2]
 mov dl,[bx+3]
 cmp dl,1
 je .numeric
 cmp dl,2
 jne .value
.numeric:
 mov ax,[ed_draw_index]
 cmp ax,[ed_field]
 jne .stage_number
 mov si,ed_number
 jmp .value
.stage_number:
 xor ax,ax
 mov al,[si]
 cmp dl,2
 jne .format
 mov ax,[si]
.format:
 mov di,ed_view_number
 call ed_format
 mov si,ed_view_number
.value:
 call ed_field_output
 inc word [ed_draw_index]
 cmp word [ed_draw_index],16
 jb .row
 mov byte [ed_attribute],0x17
 mov word [ed_position],0x1503
 mov si,ed_last_call
 call ed_string
 mov si,ed_stage+61
 mov cx,8
 xor dx,dx
 call ed_field_output
 mov si,ed_calls
 call ed_string
 mov ax,[ed_stage+70]
 mov di,ed_view_number
 call ed_format
 mov si,ed_view_number
 call ed_string
 mov word [ed_position],0x1603
 mov si,ed_keys
 call ed_string
 mov word [ed_position],0x1703
 mov si,ed_overwrite
 cmp byte [ed_insert],0
 je .status
 mov si,ed_inserting
.status:
 cmp byte [ed_error],0
 je .message
 mov si,ed_invalid
.message:
 call ed_string
 mov ax,[ed_field]
 add al,4
 mov dh,al
 mov ax,[ed_cursor]
 add al,23
 mov dl,al
 mov bh,[ed_page]
 mov ah,2
 call ed_bios
 ret
; SI/CX raw bounded field; DL3 masks password. Other controls sanitize.
ed_field_output:
 xor bx,bx
.next:
 lodsb
 or al,al
 jz .pad
 or bx,bx
 jnz .pad
 cmp dl,3
 jne .sanitize
 mov al,'*'
 jmp .put
.sanitize:
 cmp al,32
 jb .dot
 cmp al,127
 jne .put
.dot:
 mov al,'.'
 jmp .put
.pad:
 mov bx,1
 mov al,' '
.put:
 call ed_character
 loop .next
 ret
ed_string:
 lodsb
 or al,al
 jz .done
 call ed_character
 jmp ed_string
.done:
 ret
ed_character:
 push ax
 push bx
 push cx
 push dx
 mov [ed_character_value],al
 mov dx,[ed_position]
 mov bh,[ed_page]
 mov ah,2
 call ed_bios
 mov al,[ed_character_value]
 mov ah,9
 mov bh,[ed_page]
 mov bl,[ed_attribute]
 mov cx,1
 call ed_bios
 inc byte [ed_position]
 pop dx
 pop cx
 pop bx
 pop ax
 ret
ed_bios:
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

SEGMENT _DATA public class=DATA use16
ed_record: dw 0
ed_result: dw 0
ed_saved: db 0
ed_page: db 0
ed_old_segment: dw 0
ed_video_offset: dw 0
ed_old_cursor: dw 0
ed_old_shape: dw 0
ed_field: dw 0
ed_draw_index: dw 0
ed_kind: db 0
ed_buffer: dw 0
ed_capacity: dw 0
ed_length: dw 0
ed_cursor: dw 0
ed_insert: db 0
ed_error: db 0
ed_position: dw 0
ed_attribute: db 0x17
ed_character_value: db 0
ed_number: times 6 db 0
ed_view_number: times 6 db 0
ed_digits: times 6 db 0
ed_title: db 'PCPLUS // DIRECTORY RECORD',0
ed_storage: db 'Storage editor // F10 accepts in memory // Esc discards // No file writes',0
ed_last_call: db 'Read only: last call ',0
ed_calls: db '  calls ',0
ed_keys: db 'Tab/Shift-Tab Up/Down fields  Home/End Left/Right  Ins Del Backspace',0
ed_overwrite: db 'OVERWRITE // Enter next field // F10 accept // Esc discard',0
ed_inserting: db 'INSERT // Enter next field // F10 accept // Esc discard',0
ed_invalid: db 'INVALID VALUE: correct this field; Escape always discards changes.',0
; offset,width,type(0text,1byte,2word,3password),minimum,maximum.
ed_fields:
 dw 0
 db 24,0
 dw 0,0
 dw 25
 db 20,0
 dw 0,0
 dw 46
 db 5,2
 dw 0,8
 dw 48
 db 5,1
 dw 0,4
 dw 49
 db 5,1
 dw 7,8
 dw 50
 db 5,1
 dw 1,2
 dw 51
 db 5,1
 dw 0,1
 dw 52
 db 8,0
 dw 0,0
 dw 75
 db 10,3
 dw 0,0
 dw 86
 db 8,0
 dw 0,0
 dw 95
 db 8,0
 dw 0,0
 dw 105
 db 8,0
 dw 0,0
 dw 73
 db 5,1
 dw 0,255
 dw 72
 db 5,1
 dw 0,255
 dw 74
 db 5,1
 dw 0,1
 dw 104
 db 5,1
 dw 0,8
ed_labels: dw ed_name,ed_target,ed_baud,ed_parity,ed_bits,ed_stop,ed_duplex,ed_script,ed_password,ed_key,ed_meta,ed_note,ed_profile,ed_protocol,ed_mode,ed_port
ed_name: db 'Name',0
ed_target: db 'Number / target',0
ed_baud: db 'Baud index 0..8',0
ed_parity: db 'Parity 0..4',0
ed_bits: db 'Data bits 7/8',0
ed_stop: db 'Stop bits 1/2',0
ed_duplex: db 'Duplex 0/1',0
ed_script: db 'Script',0
ed_password: db 'Password (masked)',0
ed_key: db 'KEY binding',0
ed_meta: db 'META binding',0
ed_note: db 'Note',0
ed_profile: db 'Profile 0..255',0
ed_protocol: db 'Protocol 0..255',0
ed_mode: db 'Mode 0/1',0
ed_port: db 'Port 0..8',0
ed_stage: times DD_RECORD_SIZE db 0
global ed_screen_segment
ed_screen_segment: dw seg ed_screen
SEGMENT UI_STORAGE public align=16 class=FAR_DATA use16
GROUP UI_GROUP UI_STORAGE
global ed_screen,ed_screen_end
ed_screen: resb 4000
ed_screen_end:
