; DOS self-check: actual B800 restoration, nested windows, BIOS cursor ownership.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern ui_window_save,ui_window_restore,pcplus_flow_message
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
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,2000
 mov ax,0x1e41
 rep stosw
 mov ah,2
 xor bh,bh
 mov dx,0x0711
 int 0x10
 ; Save outer2x3, paint; then save inner1x2, paint and restore both LIFO.
 mov ax,outer
 call save_outer
 or ax,ax
 jnz failed
 mov ax,0xb800
 mov es,ax
 mov word [es:324],0x4f58
 mov word [es:486],0x2e59
 mov dx,4
 push dx
 mov dx,inner
 push dx
 mov dx,2
 push dx
 mov dx,1
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 call ui_window_save
 or ax,ax
 jnz failed
 mov ax,0xb800
 mov es,ax
 mov word [es:324],0x5a5a
 mov dx,4
 push dx
 mov dx,inner
 push dx
 mov dx,2
 push dx
 mov dx,1
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 call ui_window_restore
 or ax,ax
 jnz failed
 mov ax,0xb800
 mov es,ax
 cmp word [es:324],0x4f58
 jne failed
 mov dx,12
 push dx
 mov dx,outer
 push dx
 mov dx,3
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 call ui_window_restore
 or ax,ax
 jnz failed
 mov ax,0xb800
 mov es,ax
 cmp word [es:324],0x1e41
 jne failed
 cmp word [es:486],0x1e41
 jne failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0711
 jne failed
 ; Zero duration leaves the original flow overlay painted.
 xor ax,ax
 push ax
 mov ax,message_flow
 push ax
 call pcplus_flow_message
 add sp,4
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x1e20
 jne failed
 cmp word [es:2],0x1e46
 jne failed
 ; Nonzero duration waits actual BIOS ticks and restores the previous overlay.
 mov ax,1
 push ax
 mov ax,message_wait
 push ax
 call pcplus_flow_message
 add sp,4
 mov ax,0xb800
 mov es,ax
 cmp word [es:2],0x1e46
 jne failed
 cmp word [es:8],0x1e57
 jne failed
 cmp word [es:30],0x1e41
 jne failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0711
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
save_outer:
 mov dx,12
 push dx
 push ax
 mov dx,3
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 mov dx,2
 push dx
 call ui_window_save
 ret
SEGMENT _DATA public align=16 class=DATA use16
global text_video_segment,text_cga_status_port,screen_columns,ui_window_rows,window_buffer
text_video_segment: dw 0xb800
text_cga_status_port: dw 0
screen_columns: dw 80
ui_window_rows: dw 25
global ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base,ui_flow_suppressed,ui_flow_attribute
ui_flow_region_cells: dw 80
ui_flow_video_base: dw 0
ui_flow_coordinate_base: dw 0
ui_flow_suppressed: dw 0
ui_flow_attribute: dw 0x1e
message_flow: db 'FLOW',0
message_wait: db 'WAIT',0
outer: times 12 db 0
inner: times 4 db 0
window_buffer: times 4096 db 0xa5
SEGMENT STACK stack align=16 class=STACK use16
resb 4096
stack_top:
