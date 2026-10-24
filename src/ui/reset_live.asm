; Experimental field-aware width transaction for1..25 content rows. Native owns its
; projected bank and physical content rows. Root metadata is committed only
; after validation; UART, connection, parser, handles and RIS defaults never
; enter this projection. Peer mode dispatch retains the native RET2 ABI.
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
extern redisplay_snapshot,program_screen,redisplay_live
extern _redisplay_active,_redisplay_export_pending,_redisplay_search_pending,_command_menu_active
extern terminal_program_active,terminal_program_pending,terminal_macro_active
extern terminal_monitor_active,terminal_snapshot_active,terminal_screen_print_active
extern terminal_controller_active,terminal_ansi_wait_active,terminal_transfer_active,terminal_transfer_pending
extern reset_ready,connection_state,text_video_segment,text_cga_status_port
extern terminal_browser_screen_owned,terminal_editor_screen_owned,terminal_aspect_active
extern terminal_width_aspect_owner_far,_redisplay_live_ready
extern csi_unimplemented_service,terminal_peer_width_abort_far
extern screen_attributes_base,screen_attribute_cells,erase_attribute_values_base,erase_attribute_values
extern erase_shadow_offset,erase_shadow_segment,erase_shadow_cells
extern ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,ui_flow_suppressed,csi_row_count
extern screen_line_flags,terminal_tab_stops,terminal_viewport_admit_far
extern csi_saved_row,csi_saved_column,csi_wrap_pending,cursor_state_saved_3342
extern nreset_terminal_reset_geometry_native,nreset_erase_repair_attributes
extern nreset_screen_cursor_wrap,nreset_screen_attribute_checks,nreset_erase_protection_mode
extern csi_erase_attribute,nreset_csi_erase_attribute
extern nreset_screen_attributes_base,nreset_screen_attribute_cells
extern nreset_erase_attribute_values_base,nreset_erase_attribute_values
extern nreset_erase_shadow_offset,nreset_erase_shadow_segment,nreset_reset_shadow_bytes
extern nreset_reset_geometry_initialized,nreset_reset_wide_mode,nreset_reset_configured_wide
extern nreset_program_state_7a72,nreset_program_state_7a74,nreset_reset_video_cells
extern nreset_reset_status_hidden,nreset_text_video_segment,nreset_text_cga_status_port
extern nreset_screen_line_flags,nreset_terminal_tab_stops,nreset_screen_set_cursor
extern nreset_terminal_reset_width_native,nreset_screen_top_margin,nreset_screen_bottom_margin
global terminal_native_width_far,reset_live_prepare,reset_live_finish
global reset_live_active,reset_live_validate,reset_live_commit,reset_live_rollback
reset_live_active: dw 0
live_request: dw 0
live_result: dw 0
saved_cursor: dw 0
saved_shape: dw 0
live_rows: dw 0
live_cells: dw 0
live_shadow_words: dw 0
global live_backup_offset,live_backup_segment
live_backup_offset: dw program_screen
live_backup_segment: dw seg program_screen

; Native mode3 adapter is callee-cleaned in resident code. Any refusal uses
; the established terminal/ASPECT unwind rather than continuing half a mode.
global terminal_peer_width_far
terminal_peer_width_far:
 call far terminal_native_width_far
 or ax,ax
 jnz .bad
 retf
.bad:
 mov ax,0x2a6e
 mov [csi_unimplemented_service],ax
 jmp far terminal_peer_width_abort_far

; Each row explicitly declares root/native offsets and whether native output
; may be committed (high bit of the root offset). Link inspection verifies
; every root offset fits15 bits. No pointer/parser/reset baseline is writable.
%macro field 2
 extern %1,nreset_ %+ %1
 dw %1 + (%2 << 15),nreset_ %+ %1
%endmacro
global reset_live_projection,reset_live_projection_end
reset_live_projection:
projection:
 field csi_terminal_id,0
 field attributes_normal_value,0
 field attributes_preset_value,0
 field attributes_current,1
 field attributes_monochrome,0
 field screen_columns,0
 field screen_video_row_bytes,0
 field screen_attribute_row_bytes,1
 field screen_last_column,1
 field csi_last_row,1
 field screen_first_row,1
 field screen_last_row,1
 field csi_origin_row,1
 field csi_origin_bottom,1
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
 dw csi_row_count + 0x8000,nreset_program_state_7a74
reset_live_projection_end:
PROJECTION_COUNT equ ($-projection)/4
; Declarative admission keeps the resident implementation compact without
; weakening any layout/owner constraint as more native services are linked.
common_layout:
 dw reset_ready,1
 dw screen_vertical_attribute_check,0,screen_reverse_wrap_blocked,0
 dw terminal_tab_wrap,0,terminal_dec_keys,1
 dw screen_use_bios_cursor,1,screen_columns,80
 dw screen_video_row_bytes,160,screen_viewport_right,79
 dw screen_attributes_base,screen_attribute_cells
 dw erase_attribute_values_base,erase_attribute_values
 dw erase_shadow_segment,seg erase_shadow_cells,erase_shadow_offset,erase_shadow_cells
 dw text_video_segment,0xb800,text_cga_status_port,0
 dw ui_flow_region_cells,80,ui_flow_video_base,3840,ui_flow_coordinate_base,0x1800
COMMON_COUNT equ ($-common_layout)/4
narrow_layout:
 dw screen_attribute_row_bytes,80,screen_last_column,79
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
 ; ASPECT already owns program_screen. Its transaction uses the separate,
 ; idle editor/viewer live backup selected by the admission below.
 mov ax,[cs:live_backup_segment]
 mov es,ax
 mov di,[cs:live_backup_offset]
 push ds
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov cx,[cs:live_cells]
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
 cmp byte [terminal_browser_screen_owned],0
 jne .bad_owner
 cmp byte [terminal_editor_screen_owned],0
 jne .bad_owner
 cmp word [_redisplay_live_ready],0
 jne .bad_owner
 mov word [cs:live_backup_offset],program_screen
 mov word [cs:live_backup_segment],seg program_screen
 cmp word [terminal_program_active],0
 je .foreground_owner
 call far terminal_width_aspect_owner_far
 jc .bad_owner
 mov word [cs:live_backup_offset],redisplay_live
 mov word [cs:live_backup_segment],seg redisplay_live
 jmp .other_owners
.foreground_owner:
 cmp word [terminal_aspect_active],0
 jne .bad_owner
.other_owners:
 mov ax,[terminal_program_pending]
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
 jnz .bad_owner
 mov ax,[connection_state]
 or ax,ax
 jz .profile
 cmp ax,6
 jne .bad_owner
.profile:
 mov ax,[csi_terminal_id]
 cmp ax,4
 je .plain
 cmp ax,6
 jne .bad_owner
 jmp .plain
.bad_owner:
 stc
 ret
.plain:
 cmp word [screen_attribute_checks],1
 ja .bad_rows
 cmp word [screen_cursor_wrap],1
 ja .bad_rows
 cmp word [erase_protection_mode],1
 ja .bad_rows
 mov si,common_layout
 mov cx,COMMON_COUNT
 call match_layout
 jc .bad_rows
 mov ax,[csi_row_count]
 cmp ax,1
 jb .bad_rows
 cmp ax,25
 ja .bad_rows
 mov dx,ax
 dec ax
 cmp ax,[csi_last_row]
 jne .bad_rows
 cmp [screen_last_row],ax
 ja .bad_rows
 mov ax,[screen_first_row]
 cmp ax,[screen_last_row]
 ja .bad_rows
 mov ax,[screen_cursor_row]
 cmp ax,[csi_last_row]
 ja .bad_rows
 mov ax,[screen_cursor_column]
 cmp ax,[screen_last_column]
 ja .bad_rows
 ; Keep a visible physical status row outside the transaction. The legacy
 ; narrow startup exposes25 rows; its first width reset adopts24 content rows.
 cmp word [ui_flow_suppressed],1
 ja .bad_rows
 jne .visible
 jmp .rows
.visible:
 cmp dx,25
 jne .rows
 cmp word [screen_attribute_row_bytes],80
 jne .bad_rows
 dec dx
 jmp .rows
.bad_rows:
 stc
 ret
.rows:
 mov [cs:live_rows],dx
 mov ax,80
 mul dx
 mov [cs:live_cells],ax
 mov ax,132
 mul word [cs:live_rows]
 mov [cs:live_shadow_words],ax
 mov ax,[screen_attribute_row_bytes]
 mul word [csi_row_count]
 cmp ax,[erase_cell_count]
 jne .bad_layout
 cmp word [screen_attribute_row_bytes],132
 je .wide
 mov si,narrow_layout
 mov cx,NARROW_COUNT
 call match_layout
 jc .bad_layout
 cmp word [screen_viewport_active],1
 ja .bad_layout
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x49],3
 jne .bad_layout
 cmp word [es:0x4a],80
 jne .bad_layout
 cmp byte [es:0x62],0
 jne .bad_layout
 cmp byte [es:0x84],0
 je .okay
 cmp byte [es:0x84],24
 jne .bad_layout
 jmp .okay
.bad_layout:
 stc
 ret
.okay:
 ; A stable public transaction boundary must have coherent cursor caches;
 ; unlike the pane's internal callback, it never admits an intermediate pan.
 mov ax,[screen_cursor_row]
 cmp ax,[screen_previous_row]
 jne .bad
 mov ax,[screen_cursor_column]
 cmp ax,[screen_previous_column]
 jne .bad
 sub ax,[screen_viewport_offset]
 jc .bad
 cmp ax,[screen_visible_column]
 jne .bad
 shl ax,1
 mov bx,ax
 mov ax,[screen_cursor_row]
 mov cx,160
 mul cx
 add ax,bx
 cmp ax,[screen_video_offset]
 jne .bad
 mov ax,[screen_cursor_row]
 mul word [screen_attribute_row_bytes]
 add ax,[screen_cursor_column]
 cmp ax,[screen_attribute_offset]
 jne .bad
 clc
 ret
.wide:
 call far terminal_viewport_admit_far
 jc .bad
 jmp .okay
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
 and bx,0x7fff
 mov di,[cs:si+2]
 mov ax,[es:bx]
 mov [di],ax
 add si,4
 loop .fields
 ; The root erase attribute is a byte followed by an independent mode word.
 mov al,[es:csi_erase_attribute]
 mov [nreset_csi_erase_attribute],al
 mov word [nreset_screen_attributes_base],nreset_screen_attribute_cells
 mov word [nreset_erase_attribute_values_base],nreset_erase_attribute_values
 mov word [nreset_program_state_7a72],80
 mov ax,[cs:live_rows]
 mov [nreset_program_state_7a74],ax
 dec ax
 mov [nreset_csi_last_row],ax
 mov [nreset_screen_last_row],ax
 mov [nreset_screen_bottom_margin],ax
 mov word [nreset_screen_first_row],0
 mov word [nreset_screen_top_margin],0
 mov ax,[cs:live_cells]
 mov [nreset_reset_video_cells],ax
 mov ax,[nreset_screen_attribute_row_bytes]
 mul word [cs:live_rows]
 mov [nreset_erase_cell_count],ax
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
 mov ax,[cs:live_shadow_words]
 shl ax,1
 mov [nreset_reset_shadow_bytes],ax
 mov ax,1
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
 mov cx,3300
 rep movsb
 mov si,erase_attribute_values
 mov di,nreset_erase_attribute_values
 mov cx,3300
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
 mov cx,3300
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

; Retain the recovered width instructions and their ABI; derive the count
; from the admitted row owner instead of their original24-row constants.
global nreset_terminal_reset_width
nreset_terminal_reset_width:
 push bp
 mov bp,sp
 push word [bp+4]
 call nreset_terminal_reset_width_native
 pushf
 push ax
 push dx
 mov ax,[nreset_screen_attribute_row_bytes]
 mul word [nreset_program_state_7a74]
 mov [nreset_erase_cell_count],ax
 pop dx
 pop ax
 popf
 mov sp,bp
 pop bp
 ret

; Keep native geometry/allocation, replacing its fixed24-row field reshape.
; DS=SS=native bank. The native second argument is only a metadata-move gate.
; A full reset retains its existing owner; live width calls pass zero.
global nreset_terminal_reset_geometry
nreset_terminal_reset_geometry:
 push bp
 mov bp,sp
 sub sp,2
 push si
 push di
 push es
 mov word [bp-2],0
 cmp word [bp+6],0
 jne .native
 mov ax,[nreset_screen_cursor_wrap]
 or ax,[nreset_screen_attribute_checks]
 or ax,[nreset_erase_protection_mode]
 jz .native
 mov word [bp-2],1
 mov si,nreset_screen_attribute_cells
 call .reshape
 mov si,nreset_erase_attribute_values
 call .reshape
.native:
 mov ax,[bp+6]
 or ax,[bp-2] ; Bypass only the native fixed-row metadata conversion.
 push ax
 push word [bp+4]
 call nreset_terminal_reset_geometry_native
 add sp,4
 cmp word [bp-2],0
 je .done
 ; Canonical left pane is needed by the native position/advance descriptors.
 mov word [nreset_screen_viewport_active],1
 mov word [nreset_screen_viewport_offset],0
 xor ax,ax
 xor dx,dx
 call nreset_screen_set_cursor
 xor ax,ax
 push ax
 call nreset_erase_repair_attributes
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 ret
.reshape:
 ; Copy overlapping rows in the direction required by width expansion or
 ; contraction. SI is a fixed4096-byte plane. Preserve all cells past the
 ; admitted destination footprint; root commit remains a separate owner.
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 sub sp,8
 mov bx,sp
 mov [ss:bx],si ; plane base
 mov ax,[nreset_screen_attribute_row_bytes]
 mov [ss:bx+2],ax ; old stride
 mov ax,80
 cmp word [cs:live_request],0
 je .target
 mov ax,132
.target:
 mov [ss:bx+4],ax ; new stride
 cmp ax,[ss:bx+2]
 je .reshape_done
 push ds
 pop es
 xor di,di
 cmp ax,[ss:bx+2]
 jb .row
 mov di,[cs:live_rows]
 dec di
.row:
 mov ax,di
 mul word [ss:bx+2]
 add ax,[ss:bx]
 mov si,ax
 mov ax,di
 mul word [ss:bx+4]
 add ax,[ss:bx]
 mov [ss:bx+6],di ; row index
 mov di,ax
 mov cx,80
 cmp word [ss:bx+4],132
 jne .forward
 ; Expanding, move each row backward so row0 and later sources survive.
 add si,79
 add di,79
 std
 rep movsb
 cld
 add di,81
 xor ax,ax
 cmp word [ss:bx],nreset_erase_attribute_values
 jne .blank
 mov ax,[nreset_attributes_normal_value]
.blank:
 mov cx,52
 rep stosb
 mov di,[ss:bx+6]
 or di,di
 jz .reshape_done
 dec di
 jmp .row
.forward:
 cld
 rep movsb
 mov di,[ss:bx+6]
 inc di
 cmp di,[cs:live_rows]
 jb .row
.reshape_done:
 cld
 add sp,8
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret

; Root DS=SS. Inspect every committed geometry/pointer before any root write.
reset_live_validate:
 mov ax,seg redisplay_snapshot
 mov es,ax
 mov si,projection
 mov cx,PROJECTION_COUNT
.readonly:
 test word [cs:si],0x8000
 jne .next
 mov bx,[cs:si]
 and bx,0x7fff
 mov di,[cs:si+2]
 mov ax,[bx]
 cmp ax,[es:di]
 jne .bad_geometry
.next:
 add si,4
 loop .readonly
 mov al,[csi_erase_attribute]
 cmp al,[es:nreset_csi_erase_attribute]
 jne .bad_geometry
 mov ax,80
 cmp word [cs:live_request],0
 je .columns
 mov ax,132
.columns:
 cmp ax,[es:nreset_screen_attribute_row_bytes]
 jne .bad_geometry
 dec ax
 cmp ax,[es:nreset_screen_last_column]
 jne .bad_geometry
 inc ax
 mul word [cs:live_rows]
 cmp ax,[es:nreset_erase_cell_count]
 jne .bad_geometry
 mov ax,[cs:live_request]
 cmp ax,[es:nreset_screen_viewport_enabled]
 jne .bad_geometry
 mov cx,52
 mul cx
 cmp ax,[es:nreset_screen_viewport_left]
 jne .bad_geometry
 cmp word [es:nreset_screen_viewport_active],1
 jne .bad_geometry
 cmp word [es:nreset_screen_viewport_offset],0
 jne .bad_geometry
 jmp .rows
.bad_geometry:
 stc
 ret
.rows:
 mov ax,[cs:live_rows]
 cmp ax,[es:nreset_program_state_7a74]
 jne .bad
 dec ax
 cmp ax,[es:nreset_csi_last_row]
 jne .bad
 cmp ax,[es:nreset_screen_last_row]
 jne .bad
 cmp ax,[es:nreset_screen_bottom_margin]
 jne .bad
 cmp word [es:nreset_screen_first_row],0
 jne .bad
 cmp word [es:nreset_screen_top_margin],0
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
 mov ax,[es:nreset_screen_previous_row]
 cmp ax,[cs:live_rows]
 jae .bad
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
 mov ax,[cs:live_shadow_words]
 shl ax,1
 cmp ax,[es:nreset_reset_shadow_bytes]
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
 test word [cs:si],0x8000
 je .next
 mov bx,[cs:si]
 and bx,0x7fff
 mov di,[cs:si+2]
 mov ax,[es:di]
 mov [bx],ax
.next:
 add si,4
 loop .fields
 ; Saved coordinates are display state too. Restoring an old bottom/right
 ; point must not leave the new logical bounds, and a wrap latch from the old
 ; edge is invalid after a cleared/home display in either width.
 mov ax,[cs:live_rows]
 dec ax
 cmp [csi_saved_row],ax
 jbe .saved_row
 mov [csi_saved_row],ax
.saved_row:
 mov ax,[es:nreset_screen_last_column]
 cmp [csi_saved_column],ax
 jbe .saved_column
 mov [csi_saved_column],ax
.saved_column:
 mov word [csi_wrap_pending],0
 mov word [cursor_state_saved_3342],0
 push ds
 mov ax,es
 mov ds,ax
 mov ax,DGROUP
 mov es,ax
 mov si,nreset_screen_attribute_cells
 mov di,screen_attribute_cells
 mov cx,3300
 rep movsb
 mov si,nreset_erase_attribute_values
 mov di,erase_attribute_values
 mov cx,3300
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
 mov cx,3300
 rep movsw
 pop ds
 ret

reset_live_rollback:
 ; No root data has been committed. Restore content only: the UART may have
 ; updated an independently owned status row since admission. Restore only
 ; admitted content (all25 rows when status is hidden).
 push ds
 mov ax,[cs:live_backup_segment]
 mov ds,ax
 mov si,[cs:live_backup_offset]
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,[cs:live_cells]
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
