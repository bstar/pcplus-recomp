; Maintained static-shadow admission around recovered viewport instructions.
; Peer width requests remain a separate owner; this never allocates or resets
; the application data image. Pane copies cannot own the status/modal rows.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
NEAR_ENTRY screen_viewport_enter
NEAR_ENTRY screen_viewport_leave
NEAR_ENTRY screen_viewport_refresh
NEAR_ENTRY terminal_viewport_admit
extern ui_cga_blank,ui_cga_unblank,terminal_capture_native_refresh
extern terminal_abort,csi_unimplemented_service
NEAR_NAMED_SERVICE viewport_blank,ui_cga_blank
NEAR_NAMED_SERVICE viewport_unblank,ui_cga_unblank
NEAR_NAMED_SERVICE viewport_capture,terminal_capture_native_refresh
viewport_abort_resident:
 mov [csi_unimplemented_service],ax
 jmp terminal_abort

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
FAR_ENTRY screen_viewport_enter
FAR_ENTRY screen_viewport_leave
FAR_ENTRY screen_viewport_refresh
FAR_ENTRY terminal_viewport_admit
FAR_SERVICE viewport_blank
FAR_SERVICE viewport_unblank
FAR_SERVICE viewport_capture
global viewport_cga_blank,viewport_cga_unblank
viewport_cga_blank: jmp viewport_blank_service
viewport_cga_unblank: jmp viewport_unblank_service
extern viewport_enter,viewport_leave
extern screen_columns,screen_video_row_bytes,screen_attribute_row_bytes
extern screen_viewport_enabled,screen_viewport_active,screen_viewport_offset
extern screen_viewport_left,screen_viewport_right,screen_last_column
extern csi_row_count,csi_last_row,screen_first_row,screen_last_row,erase_cell_count
extern screen_attributes_base,screen_attribute_cells
extern erase_attribute_values_base,erase_attribute_values
extern erase_shadow_offset,erase_shadow_segment,erase_shadow_cells
extern text_video_segment,text_cga_status_port,ui_flow_suppressed
extern ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base
extern csi_terminal_id,reset_ready,connection_state
extern terminal_program_active,terminal_program_pending,terminal_macro_active
extern terminal_monitor_active,terminal_snapshot_active,terminal_screen_print_active
extern terminal_controller_active,terminal_ansi_wait_active
extern terminal_transfer_active,terminal_transfer_pending
extern _redisplay_active,_command_menu_active

%macro save 0
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
%endmacro
%macro restore 0
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
%endmacro

screen_viewport_enter_impl:
 call terminal_viewport_admit_impl
 jc .bad
 cmp word [screen_viewport_active],0
 jne .bad
 save
 call viewport_enter
 restore
 ret
.bad:
 mov ax,0x482a
 call far viewport_abort_resident
screen_viewport_leave_impl:
 call terminal_viewport_admit_impl
 jc .bad
 cmp word [screen_viewport_active],1
 jne .bad
 save
 call viewport_leave
 restore
 ret
.bad:
 mov ax,0x4850
 call far viewport_abort_resident

screen_viewport_refresh_impl:
 ; Capture's paired failure refresh shares the original service address, but
 ; is independent of pane copying. Consume it before interpreting viewport.
 call viewport_capture_service
 jnc .done
 call terminal_viewport_admit_impl
 jc .bad
 ; The physical status row does not change on a pan. The cursor caller commits
 ; active-pane/offset between copy and refresh, before updating cursor offsets.
.done:
 ret
.bad:
 mov ax,0x2fb8
 call far viewport_abort_resident

; Read-only plane/pane admission, CF0 valid. Preserve every general register
; and ES so the recovered cursor's pending SI/DI destination survives. Cursor
; offsets are intentionally not inspected during its intermediate pan commit.
global terminal_viewport_admit_impl
terminal_viewport_admit_impl:
 save
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
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
 or ax,[_command_menu_active]
 jnz .bad
 cmp word [connection_state],0
 je .profile
 cmp word [connection_state],6
 jne .bad
.profile:
 cmp word [reset_ready],1
 jne .bad
 mov ax,[csi_terminal_id]
 cmp ax,4
 je .geometry
 cmp ax,6
 jne .bad
.geometry:
 cmp word [screen_columns],80
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [screen_attribute_row_bytes],132
 jne .bad
 cmp word [screen_last_column],131
 jne .bad
 cmp word [screen_viewport_enabled],1
 jne .bad
 cmp word [screen_viewport_left],52
 jne .bad
 cmp word [screen_viewport_right],79
 jne .bad
 mov ax,[screen_viewport_active]
 cmp ax,1
 ja .bad
 xor ax,1
 mov cx,52
 mul cx
 cmp ax,[screen_viewport_offset]
 jne .bad
 mov ax,[csi_row_count]
 cmp ax,1
 jb .bad
 cmp ax,25
 ja .bad
 mov bx,[csi_last_row]
 inc bx
 cmp ax,bx
 jne .bad
 mov bx,[screen_last_row]
 cmp bx,ax
 jae .bad
 cmp [screen_first_row],bx
 ja .bad
 cmp word [ui_flow_suppressed],0
 jne .rows
 cmp ax,24
 ja .bad
 cmp word [ui_flow_region_cells],80
 jne .bad
 cmp word [ui_flow_video_base],3840
 jne .bad
 cmp word [ui_flow_coordinate_base],0x1800
 jne .bad
.rows:
 mov cx,132
 mul cx
 cmp ax,[erase_cell_count]
 jne .bad
 cmp word [screen_attributes_base],screen_attribute_cells
 jne .bad
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .bad
 mov ax,seg erase_shadow_cells
 cmp ax,[erase_shadow_segment]
 jne .bad
 cmp word [erase_shadow_offset],erase_shadow_cells
 jne .bad
 cmp word [text_video_segment],0xb800
 jne .bad
 cmp word [text_cga_status_port],0
 jne .bad ; Native CGA retrace wait has no bounded live owner yet.
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
 restore
 clc
 ret
.bad:
 restore
 stc
 ret
