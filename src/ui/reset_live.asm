; Experimental plain24-row width transaction. Native execution owns only its
; projected bank and physical content rows. Root metadata is committed only
; after validation; UART, connection, parser, handles and RIS defaults never
; enter this projection. Peer width dispatch is deliberately still unbound.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
global terminal_native_width
terminal_native_width:
 call far terminal_native_width_far
 ret

SEGMENT RESET_CODE public align=16 class=FARCODE use16
extern reset_bank_call_far,reset_bank_busy,reset_bank_abort,bank_shadow
extern redisplay_snapshot,program_screen
extern _redisplay_active,_redisplay_export_pending,_redisplay_search_pending,_command_menu_active
extern terminal_program_active,terminal_program_pending,terminal_macro_active
extern terminal_monitor_active,terminal_snapshot_active,terminal_screen_print_active
extern terminal_controller_active,terminal_ansi_wait_active,terminal_transfer_active,terminal_transfer_pending
extern reset_ready,connection_state,text_video_segment,text_cga_status_port
extern screen_attributes_base,screen_attribute_cells,erase_attribute_values_base,erase_attribute_values
extern erase_shadow_offset,erase_shadow_segment,erase_shadow_cells
extern ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,ui_flow_suppressed,csi_row_count
extern screen_line_flags,terminal_tab_stops,terminal_viewport_admit_far
extern nreset_screen_attributes_base,nreset_screen_attribute_cells
extern nreset_erase_attribute_values_base,nreset_erase_attribute_values
extern nreset_erase_shadow_offset,nreset_erase_shadow_segment,nreset_reset_shadow_bytes
extern nreset_reset_geometry_initialized,nreset_reset_wide_mode,nreset_reset_configured_wide
extern nreset_program_state_7a72,nreset_program_state_7a74,nreset_reset_video_cells
extern nreset_reset_status_hidden,nreset_text_video_segment,nreset_text_cga_status_port
extern nreset_screen_line_flags,nreset_terminal_tab_stops,nreset_screen_set_cursor
global terminal_native_width_far,reset_live_prepare,reset_live_finish
global reset_live_active,reset_live_validate,reset_live_commit,reset_live_rollback
reset_live_active: dw 0
live_request: dw 0
live_result: dw 0
saved_cursor: dw 0
saved_shape: dw 0

; Each row explicitly declares root/native offsets and whether native output
; may be committed. No pointer, parser state or reset baseline is writable here.
%macro field 2
 extern %1,nreset_ %+ %1
 dw %1,nreset_ %+ %1,%2
%endmacro
projection:
 field csi_terminal_id,0
 field attributes_normal_value,0
 field attributes_current,1
 field attributes_monochrome,0
 field screen_columns,0
 field screen_video_row_bytes,0
 field screen_attribute_row_bytes,1
 field screen_last_column,1
 field csi_last_row,0
 field screen_first_row,0
 field screen_last_row,0
 field screen_cursor_row,1
 field screen_cursor_column,1
 field screen_visible_column,1
 field screen_previous_row,1
 field screen_previous_column,1
 field screen_video_offset,1
 field screen_attribute_offset,1
 field screen_viewport_enabled,1
 field screen_viewport_active,1
 field screen_viewport_offset,1
 field screen_viewport_left,1
 field screen_viewport_right,0
 field screen_use_bios_cursor,0
 field screen_attribute_checks,0
 field screen_cursor_wrap,0
 field screen_vertical_attribute_check,0
 field screen_reverse_wrap_blocked,0
 field erase_lineflags_enabled,0
 field erase_protection_mode,0
 field erase_cell_count,1
 field terminal_dec_keys,0
 field terminal_tab_wrap,0
PROJECTION_COUNT equ ($-projection)/6
; Declarative admission keeps the resident implementation compact without
; weakening any layout/owner constraint as more native services are linked.
common_layout:
 dw reset_ready,1,screen_attribute_checks,0,screen_cursor_wrap,0
 dw screen_vertical_attribute_check,0,screen_reverse_wrap_blocked,0
 dw erase_protection_mode,0,terminal_tab_wrap,0,terminal_dec_keys,1
 dw screen_use_bios_cursor,1,csi_row_count,24,csi_last_row,23
 dw screen_first_row,0,screen_last_row,23,screen_columns,80
 dw screen_video_row_bytes,160,screen_viewport_right,79
 dw screen_attributes_base,screen_attribute_cells
 dw erase_attribute_values_base,erase_attribute_values
 dw erase_shadow_segment,seg erase_shadow_cells,erase_shadow_offset,erase_shadow_cells
 dw text_video_segment,0xb800,text_cga_status_port,0
 dw ui_flow_region_cells,80,ui_flow_video_base,3840,ui_flow_coordinate_base,0x1800
COMMON_COUNT equ ($-common_layout)/4
narrow_layout:
 dw screen_attribute_row_bytes,80,screen_last_column,79,erase_cell_count,1920
 dw screen_viewport_enabled,0,screen_viewport_left,0,screen_viewport_offset,0
NARROW_COUNT equ ($-narrow_layout)/4

%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
%endmacro
%macro restore 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
%endmacro

; AX0/1 requests80/132. Return0 committed,1 refused,3 native/output failure.
; All other registers and caller FLAGS survive. No foreground polling occurs
; inside the transaction; the UART ISR continues to own root receive state.
terminal_native_width_far:
 save
 mov bx,sp
 mov dx,ds
 mov cx,ss
 cmp dx,cx
 jne .refuse
 cmp dx,DGROUP
 jne .refuse
 mov cx,[ss:bx+18]
 and cx,0x600
 cmp cx,0x200
 jne .refuse
 cmp ax,1
 ja .refuse
 cmp word [cs:reset_live_active],0
 jne .refuse
 cmp word [cs:reset_bank_busy],0
 jne .refuse
 mov [cs:live_request],ax
 call live_admit
 jc .refuse
 mov word [cs:reset_live_active],1
 ; program_screen is disposable only while all declared modal owners are idle.
 mov ax,seg program_screen
 mov es,ax
 mov di,program_screen
 push ds
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov cx,1920
 rep movsw
 pop ds
 mov ah,3
 xor bh,bh
 int 0x10
 mov [cs:saved_cursor],dx
 mov [cs:saved_shape],cx
 mov ax,[cs:live_request]
 or ax,0x100
 call far reset_bank_call_far
 or ax,ax
 jnz .failed
 call reset_live_validate
 jc .failed
 call reset_live_commit
 mov word [cs:live_result],0
 jmp .release
.failed:
 call reset_live_rollback
 mov word [cs:live_result],3
.release:
 mov word [cs:reset_live_active],0
 jmp .return
.refuse:
 mov word [cs:live_result],1
.return:
 restore
 mov ax,[cs:live_result]
 retf

live_admit:
 mov ax,[terminal_program_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_macro_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_snapshot_active]
 or ax,[terminal_screen_print_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[terminal_transfer_active]
 or ax,[terminal_transfer_pending]
 or ax,[_redisplay_active]
 or ax,[_redisplay_export_pending]
 or ax,[_redisplay_search_pending]
 or ax,[_command_menu_active]
 jnz .bad
 mov ax,[connection_state]
 or ax,ax
 jz .profile
 cmp ax,6
 jne .bad
.profile:
 mov ax,[csi_terminal_id]
 cmp ax,4
 je .plain
 cmp ax,6
 jne .bad
.plain:
 mov si,common_layout
 mov cx,COMMON_COUNT
 call match_layout
 jc .bad
 cmp word [screen_cursor_row],23
 ja .bad
 mov ax,[screen_cursor_column]
 cmp ax,[screen_last_column]
 ja .bad
 cmp word [screen_attribute_row_bytes],132
 je .wide
 mov si,narrow_layout
 mov cx,NARROW_COUNT
 call match_layout
 jc .bad
 cmp word [screen_viewport_active],1
 ja .bad
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x49],3
 jne .bad
 cmp word [es:0x4a],80
 jne .bad
 cmp byte [es:0x62],0
 jne .bad
 cmp byte [es:0x84],0
 je .okay
 cmp byte [es:0x84],24
 jne .bad
.okay:
 clc
 ret
.wide:
 call far terminal_viewport_admit_far
 ret
.bad:
 stc
 ret

match_layout:
 mov bx,[cs:si]
 mov ax,[cs:si+2]
 cmp [bx],ax
 jne .bad
 add si,4
 loop match_layout
 clc
 ret
.bad:
 stc
 ret

; Called with DS=SS=native bank. Only ES addresses root; no C or BIOS callback
; runs while a root segment is borrowed for a straight string copy.
reset_live_prepare:
 cmp word [cs:reset_live_active],1
 jne .invalid
 mov ax,DGROUP
 mov es,ax
 mov si,projection
 mov cx,PROJECTION_COUNT
.fields:
 mov bx,[cs:si]
 mov di,[cs:si+2]
 mov ax,[es:bx]
 mov [di],ax
 add si,6
 loop .fields
 mov word [nreset_screen_attributes_base],nreset_screen_attribute_cells
 mov word [nreset_erase_attribute_values_base],nreset_erase_attribute_values
 mov word [nreset_program_state_7a72],80
 mov word [nreset_program_state_7a74],24
 mov word [nreset_reset_video_cells],1920
 mov word [nreset_reset_status_hidden],1 ; Root status owner is never native UI.
 mov word [nreset_text_video_segment],0xb800
 mov word [nreset_text_cga_status_port],0
 mov word [nreset_reset_geometry_initialized],1
 mov word [nreset_reset_configured_wide],0 ; Separate from captured root defaults.
 mov word [nreset_erase_shadow_segment],0
 mov word [nreset_erase_shadow_offset],0
 mov word [nreset_reset_shadow_bytes],0
 xor ax,ax
 cmp word [nreset_screen_attribute_row_bytes],132
 jne .width
 inc ax
 mov [nreset_erase_shadow_segment],ds
 mov word [nreset_erase_shadow_offset],bank_shadow
 mov word [nreset_reset_shadow_bytes],6336
.width:
 mov [nreset_reset_wide_mode],ax
 ; Root planes remain owned and unchanged throughout native execution.
 push ds
 pop es
 push ds
 mov ax,DGROUP
 mov ds,ax
 mov si,screen_attribute_cells
 mov di,nreset_screen_attribute_cells
 mov cx,3168
 rep movsb
 mov si,erase_attribute_values
 mov di,nreset_erase_attribute_values
 mov cx,3168
 rep movsb
 mov si,screen_line_flags
 mov di,nreset_screen_line_flags
 mov cx,128
 rep movsb
 mov si,terminal_tab_stops
 mov di,nreset_terminal_tab_stops
 mov cx,30
 rep movsb
 mov ax,seg erase_shadow_cells
 mov ds,ax
 mov si,erase_shadow_cells
 mov di,bank_shadow
 mov cx,3168
 rep movsw
 pop ds
 ret
.invalid:
 mov ax,3
 jmp reset_bank_abort

reset_live_finish:
 ; A reset clears both panes. Canonicalize the selected pane before exposing
 ; native offsets: width132 itself does not initialize the active-pane flag.
 mov word [nreset_screen_viewport_active],1
 mov word [nreset_screen_viewport_offset],0
 xor ax,ax
 xor dx,dx
 call nreset_screen_set_cursor
 ret

; Root DS=SS. Inspect every committed geometry/pointer before any root write.
reset_live_validate:
 mov ax,seg redisplay_snapshot
 mov es,ax
 mov si,projection
 mov cx,PROJECTION_COUNT
.readonly:
 cmp word [cs:si+4],0
 jne .next
 mov bx,[cs:si]
 mov di,[cs:si+2]
 mov ax,[bx]
 cmp ax,[es:di]
 jne .bad
.next:
 add si,6
 loop .readonly
 mov ax,80
 cmp word [cs:live_request],0
 je .columns
 mov ax,132
.columns:
 cmp ax,[es:nreset_screen_attribute_row_bytes]
 jne .bad
 dec ax
 cmp ax,[es:nreset_screen_last_column]
 jne .bad
 inc ax
 mov cx,24
 mul cx
 cmp ax,[es:nreset_erase_cell_count]
 jne .bad
 mov ax,[cs:live_request]
 cmp ax,[es:nreset_screen_viewport_enabled]
 jne .bad
 mov cx,52
 mul cx
 cmp ax,[es:nreset_screen_viewport_left]
 jne .bad
 cmp word [es:nreset_screen_viewport_active],1
 jne .bad
 cmp word [es:nreset_screen_viewport_offset],0
 jne .bad
 cmp word [es:nreset_program_state_7a74],24
 jne .bad
 cmp word [es:nreset_screen_attributes_base],nreset_screen_attribute_cells
 jne .bad
 cmp word [es:nreset_erase_attribute_values_base],nreset_erase_attribute_values
 jne .bad
 mov ax,[es:nreset_screen_cursor_row]
 or ax,[es:nreset_screen_cursor_column]
 or ax,[es:nreset_screen_visible_column]
 or ax,[es:nreset_screen_video_offset]
 or ax,[es:nreset_screen_attribute_offset]
 jnz .bad
 cmp word [es:nreset_screen_previous_row],23
 ja .bad
 mov ax,[es:nreset_screen_previous_column]
 cmp ax,[es:nreset_screen_last_column]
 ja .bad
 mov ax,[es:nreset_attributes_current]
 cmp ax,[attributes_normal_value]
 jne .bad
 cmp word [cs:live_request],0
 je .narrow
 mov ax,es
 cmp ax,[es:nreset_erase_shadow_segment]
 jne .bad
 cmp word [es:nreset_erase_shadow_offset],bank_shadow
 jne .bad
 cmp word [es:nreset_reset_shadow_bytes],6336
 jne .bad
 clc
 ret
.narrow:
 mov ax,[es:nreset_erase_shadow_segment]
 or ax,[es:nreset_erase_shadow_offset]
 jnz .bad
 clc
 ret
.bad:
 stc
 ret

reset_live_commit:
 mov si,projection
 mov cx,PROJECTION_COUNT
.fields:
 cmp word [cs:si+4],0
 je .next
 mov bx,[cs:si]
 mov di,[cs:si+2]
 mov ax,[es:di]
 mov [bx],ax
.next:
 add si,6
 loop .fields
 push ds
 mov ax,es
 mov ds,ax
 mov ax,DGROUP
 mov es,ax
 mov si,nreset_screen_attribute_cells
 mov di,screen_attribute_cells
 mov cx,3168
 rep movsb
 mov si,nreset_erase_attribute_values
 mov di,erase_attribute_values
 mov cx,3168
 rep movsb
 mov si,nreset_screen_line_flags
 mov di,screen_line_flags
 mov cx,128
 rep movsb
 mov si,nreset_terminal_tab_stops
 mov di,terminal_tab_stops
 mov cx,30
 rep movsb
 mov ax,seg erase_shadow_cells
 mov es,ax
 mov si,bank_shadow
 mov di,erase_shadow_cells
 mov cx,3168
 rep movsw
 pop ds
 ret

reset_live_rollback:
 ; No root data has been committed. Restore content only: the UART may have
 ; updated the physical status row since admission. Never resurrect that row.
 push ds
 mov ax,seg program_screen
 mov ds,ax
 mov si,program_screen
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,1920
 rep movsw
 pop ds
 mov dx,[cs:saved_cursor]
 mov ah,2
 xor bh,bh
 int 0x10
 mov cx,[cs:saved_shape]
 mov ah,1
 int 0x10
 ret

SEGMENT _DATA public align=16 class=DATA use16
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
