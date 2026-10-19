; Actual DOS full recovered status body + cross-segment production adapters.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
global _small_code_,status_carrier_read
extern status_renderer_refresh
_small_code_:
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,3
 int 0x10
 mov word [stack_guard],0xa55a
 mov word [stack_top],0x5aa5
 call clear_video
 call render
 mov dx,fdx_name
 call save
 mov word [meta_local_echo],1
 call clear_video
 call render
 mov dx,hdx_name
 call save
 mov word [terminal_tab_wrap],1
 mov word [reset_data_3732],1
 call clear_video
 call render
 mov dx,alt_name
 call save
 push ds
 pop es
 mov si,alternate_labels
 mov di,reset_scratch
 mov cx,88
 rep movsb
 call clear_video
 call render
 mov dx,labels_name
 call save
 mov word [reset_status_hidden],1
 call clear_video
 call render
 mov dx,hidden_name
 call save
 mov word [reset_status_hidden],0
 mov word [terminal_tab_wrap],0
 mov word [reset_data_3732],0
 mov word [reset_data_399a],1
 call clear_video
 call render
 mov dx,message_name
 call save
 mov word [reset_data_399a],0
 mov word [reset_data_46d0],invalid_format
 mov word [expected_error],3
 call clear_video
 call render
 mov dx,format_name
 call save
 mov word [reset_data_46d0],overflow_format
 mov word [expected_error],7
 call clear_video
 call render
 mov dx,overflow_name
 call save
 mov word [reset_data_46d0],arguments_format
 mov word [expected_error],10
 call clear_video
 call render
 mov dx,arguments_name
 call save
 mov ax,0x4c00
 int 0x21
render:
 mov bp,0x1234
 mov si,0x5678
 mov di,0x4321
 mov [saved_sp],sp
 call far status_renderer_refresh
 cmp ax,[expected_error]
 jne failed
 cmp sp,[saved_sp]
 jne failed
 cmp bp,0x1234
 jne failed
 cmp si,0x5678
 jne failed
 cmp di,0x4321
 jne failed
 mov ax,ds
 mov bx,ss
 cmp ax,bx
 jne failed
 cmp word [stack_guard],0xa55a
 jne failed
 cmp word [stack_top],0x5aa5
 jne failed
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne failed
 ret
failed:
 mov ax,0x4c01
 int 0x21
status_carrier_read:
 mov ax,[status_carrier]
 ret
clear_video:
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0xcccc
 mov cx,2002
 rep stosw
 ret
save:
 mov [filename],dx
 push ds
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov ax,DGROUP
 mov es,ax
 mov di,screen
 mov cx,2002
 rep movsw
 pop ds
 mov dx,[filename]
 mov ah,0x3c
 xor cx,cx
 int 0x21
 jc failed
 mov bx,ax
 mov dx,screen
 mov cx,4004
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,4004
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 ret
%include "status_renderer_state.inc"
global screen_columns,screen_viewport_enabled,screen_viewport_active
global screen_attribute_row_bytes,csi_terminal_id,terminal_tab_wrap
global terminal_sink_3988_enabled,terminal_sink_398a_enabled,terminal_sink_398c_disabled
global ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,ui_flow_attribute
global text_video_segment,text_cga_status_port
screen_columns: dw 80
screen_viewport_enabled: dw 0
screen_viewport_active: dw 0
screen_attribute_row_bytes: dw 80
csi_terminal_id: dw 4
terminal_tab_wrap: dw 0
terminal_sink_3988_enabled: dw 0
terminal_sink_398a_enabled: dw 0
terminal_sink_398c_disabled: dw 0
ui_flow_region_cells: dw 80
ui_flow_video_base: dw 3840
ui_flow_coordinate_base: dw 0x1800
ui_flow_attribute: dw 0x1e
text_video_segment: dw 0xb800
text_cga_status_port: dw 0
saved_sp: dw 0
expected_error: dw 0
filename: dw 0
fdx_name: db 'FDX.BIN',0
hdx_name: db 'HDX.BIN',0
alt_name: db 'ALT.BIN',0
labels_name: db 'LABELS.BIN',0
hidden_name: db 'HIDDEN.BIN',0
message_name: db 'MESSAGE.BIN',0
format_name: db 'FORMAT.BIN',0
overflow_name: db 'OVERFLOW.BIN',0
arguments_name: db 'ARGS.BIN',0
invalid_format: db '%03d',0
overflow_format: times 137 db 'X'
 db 0
arguments_format: times 13 db '%c'
 db 0
alternate_labels:
%macro key_label 1
 %%start: db %1,0
 times 11-($-%%start) db 0
%endmacro
key_label 'F1 HELP'
key_label 'F2 SAVE'
key_label 'F3 FIND'
key_label 'F4 SEND'
key_label 'F5 READ'
key_label 'F6 FILE'
key_label 'F7 EXIT'
key_label 'F8 MENU'
screen: times 4004 db 0
SEGMENT STACK stack align=16 class=STACK use16
stack_guard: resw 1
 resb 8192
stack_top: resw 1
