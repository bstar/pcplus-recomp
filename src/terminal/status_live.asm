; Stage parent-owned state for native STATUS. No child pointers or FILE objects.
; Far register ABI: BX=FFFF parent duplex, or byte0..255 snapshot override.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
extern status_renderer_refresh
extern ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,ui_flow_suppressed
extern screen_columns,csi_terminal_id,terminal_tab_wrap
extern terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits
extern modes_value_1d1a,terminal_program_active,_command_menu_script
global terminal_status_live,terminal_script_label_update
extern terminal_script_label_valid,terminal_script_label
terminal_status_live:
 push bp
 mov bp,sp
 sub sp,6
 mov [bp-2],bx
 cmp bx,0xffff
 je .parent
 cmp bx,255
 ja .operand
.parent:
 cmp word [ui_flow_region_cells],80
 jne .unsupported
 cmp word [ui_flow_video_base],3840
 jne .unsupported
 cmp word [ui_flow_coordinate_base],0x1800
 jne .unsupported
 cmp word [screen_columns],80
 jne .unsupported
 cmp word [csi_terminal_id],14
 ja .unsupported
 ; Native alternate labels need their own live key-label owner. The guarded
 ; script service admits the ordinary status layout until that owner exists.
 cmp word [terminal_tab_wrap],0
 jne .unsupported
 cmp word [terminal_parity],4
 ja .unsupported
 cmp word [terminal_data_bits],5
 jb .unsupported
 cmp word [terminal_data_bits],8
 ja .unsupported
 mov ax,[terminal_stop_bits]
 dec ax
 cmp ax,1
 ja .unsupported
 mov ax,[terminal_baud_low]
 mov dx,[terminal_baud_high]
 xor di,di
 xor cx,cx
.rate:
 cmp ax,[cs:status_rates+di]
 jne .next
 cmp dx,[cs:status_rates+di+2]
 je .rate_found
.next:
 add di,4
 inc cx
 cmp cx,9
 jb .rate
 jmp .unsupported
.rate_found:
 mov [bp-4],cx
 mov word [bp-6],0
 cmp word [terminal_program_active],0
 je .stage_state
 mov si,_command_menu_script
 cmp word [terminal_script_label_valid],1
 jne .invocation
 mov si,terminal_script_label
.invocation:
 mov di,si
 mov cx,64
.label_scan:
 mov al,[di]
 or al,al
 jz .label_end
 inc di
 cmp al,0x5c
 je .base
 cmp al,':'
 jne .label_next
.base:
 mov si,di
.label_next:
 loop .label_scan
 jmp .unsupported
.label_end:
 mov ax,di
 sub ax,si
 or ax,ax
 jz .unsupported
 cmp ax,14
 ja .unsupported
 mov [bp-6],si
.stage_state:
 ; A script or another explicit STATUS caller can repaint while the ordinary
 ; main-loop carrier sampler is suspended. Its cached level no longer proves
 ; that the visible row matches; the poll revalidates after ownership returns.
 mov word [status_parent_valid],0
 ; All parent/input preflights finished. These words are rendering snapshots;
 ; status drawing alone never commits a new session configuration.
 mov ax,[screen_columns]
 mov [program_state_7a72],ax
 mov ax,[ui_flow_suppressed]
 mov [reset_status_hidden],ax
 mov ax,[modes_value_1d1a]
 cmp word [bp-2],0xffff
 je .duplex
 mov ax,[bp-2]
.duplex:
 mov [meta_local_echo],ax
 mov ax,[terminal_program_active]
 mov [meta_script_active],ax
 mov word [keyboard_state_373c],0
 mov word [reset_data_3732],0
 mov word [reset_data_399a],0
 mov word [reset_data_332c],0
 mov ax,[terminal_parity]
 mov [reset_data_1b88],ax
 mov ax,[terminal_data_bits]
 mov [reset_data_1b8c],ax
 mov ax,[terminal_stop_bits]
 mov [reset_data_1b8a],ax
 mov ax,[bp-4]
 mov [reset_data_1b86],ax
 push ds
 pop es
 mov si,[bp-6]
 or si,si
 jz .refresh
 mov di,terminal_reset_script_label
.copy_label:
 lodsb
 stosb
 or al,al
 jnz .copy_label
.refresh:
 call far status_renderer_refresh
 jmp short .done
.operand:
 mov ax,7
 jmp short .done
.unsupported:
 mov ax,3
.done:
 mov sp,bp
 pop bp
 retf
 ; SI=checked parent stack label13B, BX=duplex snapshot. Roll back label on
 ; STATUS preflight failure. No child pointer enters this function.
terminal_script_label_update:
 push bp
 mov bp,sp
 sub sp,16
 push si
 push di
 push es
 push ds
 pop es
 mov dx,si
 mov ax,[terminal_script_label_valid]
 mov [bp-2],ax
 mov si,terminal_script_label
 lea di,[bp-16]
 mov cx,13
 rep movsb
 mov si,dx
 mov di,terminal_script_label
 mov cx,13
 rep movsb
 mov word [terminal_script_label_valid],1
 call far terminal_status_live
 or ax,ax
 jz .done
 mov dx,[bp-2]
 mov [terminal_script_label_valid],dx
 lea si,[bp-16]
 mov di,terminal_script_label
 mov cx,13
 rep movsb
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
status_rates: dd 300,1200,2400,4800,9600,19200,38400,57600,115200

; Ordinary main-loop scheduling only. Screen owners retain their saved frames;
; once released, a changed physical carrier repaints at most once per BIOS tick.
extern reset_ready,terminal_program_pending,terminal_aspect_active
extern terminal_parser_active,terminal_ansi_wait_active,terminal_monitor_active
extern terminal_snapshot_active,terminal_screen_print_active,terminal_controller_active
extern terminal_transfer_active,terminal_transfer_pending,_redisplay_active,_command_menu_active
extern status_uart_resident,terminal_status_notice_refresh
global terminal_status_poll
terminal_status_poll:
 pushf
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cld
 cmp word [reset_ready],1
 jne .done
 %macro defer_status 1
  cmp word [%1],0
  jne .done
 %endmacro
 defer_status terminal_program_active
 defer_status terminal_program_pending
 defer_status terminal_aspect_active
 defer_status terminal_parser_active
 defer_status terminal_ansi_wait_active
 defer_status terminal_monitor_active
 defer_status terminal_snapshot_active
 defer_status terminal_screen_print_active
 defer_status terminal_controller_active
 defer_status terminal_transfer_active
 defer_status terminal_transfer_pending
 defer_status _redisplay_active
 defer_status _command_menu_active
 defer_status ui_flow_suppressed
 defer_status terminal_tab_wrap
 %unmacro defer_status 1
 cmp word [screen_columns],80
 jne .done
 cmp word [ui_flow_region_cells],80
 jne .done
 cmp word [ui_flow_video_base],3840
 jne .done
 cmp word [ui_flow_coordinate_base],0x1800
 jne .done
 cmp word [csi_terminal_id],14
 ja .done
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 cmp ax,[status_parent_tick]
 je .done
 mov [status_parent_tick],ax
 call far status_uart_resident
 cmp word [status_parent_valid],1
 jne .changed
 cmp ax,[status_parent_carrier]
 je .done
.changed:
 mov bx,ax
 call far terminal_status_notice_refresh
 or ax,ax
 jnz .done
 mov [status_parent_carrier],bx
 mov word [status_parent_valid],1
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 popf
 mov ax,0
 retf

SEGMENT _TEXT public class=CODE use16
extern uart_carrier_detect
global status_carrier_read
status_carrier_read: jmp uart_carrier_detect

%include "src/status/status_state.inc"

SEGMENT _DATA
global status_parent_tick,status_parent_valid,status_parent_carrier
status_parent_tick: dw 0
status_parent_valid: dw 0
status_parent_carrier: dw 0
