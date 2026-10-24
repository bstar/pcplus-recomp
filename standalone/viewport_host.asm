; Source-owned far-buffer fixture. No allocation or production UI substitution.
BITS 16
CPU 8086
GROUP DGROUP _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern viewport_copy
global viewport_invoke
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,terminal_stack_top
 sti
 cld
 mov ax,0xb800
 mov es,ax
 mov word [es:0],0x1e51
 mov word [es:2],0x1e52
 mov word [es:4],0x1e53
 mov word [es:6],0x1e54
 call viewport_invoke
 mov word [viewport_flags],0x8001
 call viewport_invoke
 cmp word [es:0],0x1e52
 jne failed
 cmp word [es:2],0x1043
 jne failed
 cmp word [es:4],0x1e54
 jne failed
 cmp word [es:6],0x1046
 jne failed
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
viewport_invoke:
 push word [viewport_flags]
 call viewport_copy
 ret
SEGMENT _DATA public class=DATA use16
global viewport_flags,viewport_physical_columns,viewport_rows,screen_viewport_left
global text_video_segment,erase_shadow_offset,erase_shadow_segment
global screen_viewport_active,text_cga_status_port
viewport_flags: dw 0
viewport_physical_columns: dw 2
viewport_rows: dw 2
screen_viewport_left: dw 1
text_video_segment: dw 0xb800
erase_shadow_offset: dw shadow_cells
erase_shadow_segment: dw seg shadow_cells
screen_viewport_active: dw 0
; Deliberately differ from native7A8Eh; leave room outside owned copy extents.
times 0x7b00-($-$$) db 0
text_cga_status_port: dw 0
SEGMENT _VIEW_SHADOW public class=FAR_DATA use16
times 16 db 0xa5
global shadow_cells
shadow_cells: dw 0x1041,0x1042,0x1043,0x1044,0x1045,0x1046
times 16 db 0xa5
SEGMENT STACK stack class=STACK use16
resb 2048
global terminal_stack_top
terminal_stack_top:
