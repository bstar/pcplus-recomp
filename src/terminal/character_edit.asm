; Maintained live bounds around actual recovered ICH/DCH/HTS instructions.
; Ordinary80-column layouts use recovered helpers. Owned132-column layouts
; use the logical-row owner; unsupported layouts remain bounded no-ops.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern csi_insert_character,csi_delete_character,terminal_set_tab,terminal_abort
extern ansi_parameters,screen_cursor_row,screen_cursor_column,csi_last_row
extern screen_last_column,screen_columns,screen_video_row_bytes
extern screen_attribute_row_bytes,screen_video_offset,screen_attribute_offset
extern screen_viewport_active,screen_viewport_offset,text_video_segment,screen_viewport_enabled
extern screen_line_flags,screen_cursor_wrap,screen_attribute_checks
extern screen_attributes_base,screen_attribute_cells
extern erase_attribute_values_base,erase_attribute_values
extern attribute_repair_admit_far,character_wide_edit_far,character_wide_prepare_far
global csi_service_d270,csi_service_d440,ansi_escape_service_dac6

global terminal_character_prepare
; Validate the repetition bound before the dispatcher's unconditional final
; call. Clipping only inside a helper would execute one extra clipped unit.
terminal_character_prepare:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 cmp word [screen_attribute_row_bytes],132
 jne .ordinary
 call far character_wide_prepare_far
 jmp .done
.ordinary:
 call character_edit_prepare
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret

csi_service_d270:
 push bp
 push si
 push di
 push es
 xor di,di
 cmp word [screen_attribute_row_bytes],132
 je .wide
 call character_edit_prepare
 jc .failed
 call csi_insert_character
 jmp .done
.wide:
 call far character_wide_edit_far
 jmp .done
.failed:
 or ax,ax
 jz .done
 jmp terminal_abort
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

csi_service_d440:
 push bp
 push si
 push di
 push es
 mov di,1
 cmp word [screen_attribute_row_bytes],132
 je .wide
 call character_edit_prepare
 jc .failed
 call csi_delete_character
 jmp .done
.wide:
 call far character_wide_edit_far
 jmp .done
.failed:
 or ax,ax
 jz .done
 jmp terminal_abort
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; DI0 insert/1 delete. Clip the outer dispatcher's signed repetition count.
; No-op invalid state also sets count1 so the parser cannot loop32767 times.
character_edit_prepare:
 call far character_edit_prepare_far
 ret

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
global character_edit_prepare_far
character_edit_prepare_far:
 cmp word [screen_columns],80
 jne .outside
 cmp word [screen_attribute_row_bytes],80
 jne .outside
 cmp word [screen_video_row_bytes],160
 jne .outside
 cmp word [text_video_segment],0xb800
 jne .outside
 cmp word [screen_viewport_active],1
 ja .outside
 cmp word [screen_viewport_offset],0
 jne .outside
 cmp word [screen_viewport_enabled],0
 jne .outside
 cmp word [csi_last_row],24
 ja .outside
 mov ax,[screen_cursor_row]
 cmp ax,[csi_last_row]
 ja .outside
 mov bx,ax
 mov cx,80
 mul cx
 add ax,[screen_cursor_column]
 cmp ax,[screen_attribute_offset]
 jne .outside
 shl ax,1
 cmp ax,[screen_video_offset]
 jne .outside
 mov dx,[screen_last_column]
 cmp dx,79
 ja .outside
 mov ax,[screen_cursor_column]
 cmp ax,dx
 ja .outside
 sub dx,ax
 inc dx
 test byte [screen_line_flags+bx],0x40
 jz .width_ready
 test al,1
 jnz .outside
 ; The exact two-cell helper requires its full final pair to fit.
 test byte [screen_last_column],1
 jz .outside
 shr dx,1
.width_ready:
 cmp word [screen_cursor_wrap],0
 jne .metadata
 cmp word [screen_attribute_checks],0
 je .count
.metadata:
 cmp word [screen_attributes_base],screen_attribute_cells
 jne .outside
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .outside
 cmp word [screen_attribute_checks],0
 jne .protected_count
 or di,di
 jz .count
 ; Check the whole remaining metadata span, not just the first deleted byte.
 ; A later repeated helper can reach2D98 after earlier video/plane movement.
 ; Validate the actual repair geometry before the first helper runs.
 mov si,[screen_attribute_offset]
 add si,screen_attribute_cells
 mov cx,[screen_last_column]
 sub cx,[screen_cursor_column]
 inc cx
.scan:
 test byte [si],0x80
 jnz .repair_ready
 inc si
 loop .scan
 jmp .count
.repair_ready:
 call far attribute_repair_admit_far
 jc .unsupported_attributes
 jmp .count
.protected_count:
 mov si,[screen_attribute_offset]
 add si,[screen_attributes_base]
 mov cx,[screen_last_column]
 sub cx,[screen_cursor_column]
 inc cx
 xor ax,ax
.field_scan:
 test byte [si],0x81
 jnz .field_end
 inc si
 inc ax
 loop .field_scan
.field_end:
 test byte [screen_line_flags+bx],0x40
 jz .field_units
 shr ax,1
.field_units:
 or ax,ax
 jz .outside
 cmp dx,ax
 jbe .count
 mov dx,ax
.count:
 mov ax,[ansi_parameters]
 cmp ax,1
 jge .positive
 mov ax,1
.positive:
 cmp ax,dx
 jbe .store
 mov ax,dx
.store:
 mov [ansi_parameters],ax
 clc
 retf
.outside:
 mov word [ansi_parameters],1
 xor ax,ax
 stc
 retf
.unsupported_attributes:
 mov ax,0x2d98
 stc
 retf

SEGMENT _TEXT
; AX0 insert/1 delete. Keyboard admission precedes all wire/echo effects.
; Preserve parser count and caller registers; unsupported layouts return3.
global terminal_key_edit_admit_far,terminal_key_edit_far
terminal_key_edit_admit_far:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push word [ansi_parameters]
 mov di,ax
 call character_edit_prepare
 jc .reject
 xor ax,ax
 jmp .restore
.reject:
 mov ax,3
.restore:
 pop word [ansi_parameters]
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

; One original helper call, after checked keyboard admission. No CSI count.
terminal_key_edit_far:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 or ax,ax
 jnz .delete
 call csi_insert_character
 jmp .done
.delete:
 call csi_delete_character
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf

ansi_escape_service_dac6:
 push bp
 push si
 push di
 push es
 cmp word [screen_columns],80
 jne .done
 cmp word [screen_cursor_row],24
 ja .done
 mov ax,[screen_last_column]
 cmp ax,79
 ja .done
 cmp [screen_cursor_column],ax
 ja .done
 call terminal_set_tab
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
