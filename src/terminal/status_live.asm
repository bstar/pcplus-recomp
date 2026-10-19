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
 mov di,terminal_reset_script_label
.copy_label:
 lodsb
 stosb
 or al,al
 jnz .copy_label
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

SEGMENT _TEXT public class=CODE use16
extern uart_carrier_detect
global status_carrier_read
status_carrier_read: jmp uart_carrier_detect

%include "src/status/status_state.inc"
