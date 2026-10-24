; Declared width fixture plus passive ASPECT lease/window and exit observers.
BITS 16
CPU 8086
ORG 100h
%include "wide_viewer_offsets.inc"
jmp start
old10: dw 0,0
old21: dw 0,0
old1c: dw 0,0
live_call: dw LIVE_OFF,0
sample:
 dw 0x5756
staged: dw 0
width_result: dw 0xffff
exits: dw 0
exit_status: dw 0xffff
root_ds: dw 0
root_ss: dw 0
cell_count: dw 0
cursor_row: dw 0
cursor_column: dw 0
wrap: dw 0
checks: dw 0
protection: dw 0
pane: dw 0
pending_ticks: dw 0
queued_ticks: dw 0
%ifndef COMPACT_OBSERVER
video: times 4000 db 0
shadow: times 8192 db 0
flags: times 4096 db 0
values: times 4096 db 0
frame_count: dw 0
viewer_ticks: dw 0
frames: times 48*320 db 0
%endif
aspect_attached_ticks: dw 0
aspect_bridge_ticks: dw 0
aspect_overlay_ticks: dw 0
sample_end:
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
 cld
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
handler10:
 save
 cmp ah,2
 jne .done
 cmp word [cs:staged],0
 jne .done
 cmp dx,0x0511
 jne .done
 cmp word [SCREEN_COLUMNS],80
 jne .done
 cmp word [SCREEN_ATTRIBUTES_BASE],SCREEN_ATTRIBUTE_CELLS
 jne .done
 cmp word [ERASE_ATTRIBUTE_VALUES_BASE],ERASE_ATTRIBUTE_VALUES
 jne .done
 pushf
 call far [cs:old10]
 mov [cs:root_ds],ds
 inc word [cs:staged]
 mov ax,ds
 sub ax,DGROUP_REL
 add ax,LIVE_CODE_REL
 mov [cs:live_call+2],ax
%ifdef HIDDEN_STATUS
 mov word [UI_FLOW_SUPPRESSED],1
%endif
 push ds
 pop es
 mov di,SCREEN_ATTRIBUTE_CELLS
 xor ax,ax
 mov cx,4096
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov cx,4096
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,7
 mov cx,2000
 rep stosb
 mov byte [SCREEN_ATTRIBUTE_CELLS+5*80+17],0x80
 mov byte [SCREEN_ATTRIBUTE_CELLS+5*80+79],0x81
 mov byte [SCREEN_ATTRIBUTE_CELLS+6*80],0x80
 mov di,ERASE_ATTRIBUTE_VALUES+5*80+17
 mov al,0x1e
 mov cx,62
 rep stosb
 mov al,0x2a
 stosb
 mov di,ERASE_ATTRIBUTE_VALUES+6*80
 mov al,0x3e
 mov cx,2000-6*80
 rep stosb
 mov word [SCREEN_CURSOR_WRAP],1
 mov word [SCREEN_ATTRIBUTE_CHECKS],1
 mov word [ERASE_PROTECTION_MODE],1
 mov word [ATTRIBUTES_PRESET_VALUE],0x4e
 mov byte [CSI_ERASE_ATTRIBUTE],7
 mov ax,1
 sti
 call far [cs:live_call]
 cli
 mov [cs:width_result],ax
.done:
 restore
 jmp far [cs:old10]
handler1c:
 save
 cmp word [cs:staged],1
 jne .done
 mov ax,[cs:root_ds]
 mov es,ax
 push es
 sub ax,DGROUP_REL
 add ax,ASPECT_CODE_REL
 mov es,ax
 cmp word [es:RENDER_ATTACHED],1
 jne .aspect_done
 inc word [cs:aspect_attached_ticks]
 cmp word [es:RESIDENT_BRIDGE_BUSY],1
 jne .aspect_overlay
 inc word [cs:aspect_bridge_ticks]
.aspect_overlay:
 cmp word [es:TERMINAL_SCRIPT_OVERLAY_VISIBLE],1
 jne .aspect_done
 inc word [cs:aspect_overlay_ticks]
.aspect_done:
 pop es
%ifndef COMPACT_OBSERVER
 cmp word [es:TERMINAL_MENU_PENDING],1
 jne .viewer
 inc word [cs:pending_ticks]
 cmp word [es:TERMINAL_PARSER_ACTIVE],1
 jne .viewer
 cmp word [es:TERMINAL_DEFERRED_COUNT],2
 jb .viewer
 inc word [cs:queued_ticks]
.viewer:
 cmp word [es:REDISPLAY_ACTIVE],1
 jne .done
 cmp word [es:REDISPLAY_LIVE_READY],0
 jne .done
 push cs
 pop ds
 inc word [viewer_ticks]
 mov ax,[viewer_ticks]
 xor dx,dx
 mov bx,3
 div bx
 or dx,dx
 jnz .done
 cmp word [frame_count],48
 jae .done
 mov ax,320
 mul word [frame_count]
 mov si,frames
 add si,ax
 mov ax,0xb800
 mov es,ax
 xor di,di
 call .row
 mov di,320
 call .row
 mov di,800
 call .row
 mov di,3840
 call .row
 inc word [frame_count]
%endif
.done:
 restore
 jmp far [cs:old1c]
%ifndef COMPACT_OBSERVER
.row:
 mov cx,80
.next:
 mov al,[es:di]
 mov [si],al
 inc si
 add di,2
 loop .next
 ret
%endif
handler21:
 save
 cmp ah,0x4c
 jne .done
 cmp word [cs:staged],1
 jne .done
 cmp word [cs:exits],0
 jne .done
 mov bx,ds
 cmp bx,[cs:root_ds]
 jne .done
 xor ah,ah
 mov [cs:exit_status],ax
 mov [cs:root_ss],ss
 mov ax,[ERASE_CELL_COUNT]
 mov [cs:cell_count],ax
 mov ax,[SCREEN_CURSOR_ROW]
 mov [cs:cursor_row],ax
 mov ax,[SCREEN_CURSOR_COLUMN]
 mov [cs:cursor_column],ax
 mov ax,[SCREEN_CURSOR_WRAP]
 mov [cs:wrap],ax
 mov ax,[SCREEN_ATTRIBUTE_CHECKS]
 mov [cs:checks],ax
 mov ax,[ERASE_PROTECTION_MODE]
 mov [cs:protection],ax
 mov ax,[SCREEN_VIEWPORT_ACTIVE]
 mov [cs:pane],ax
%ifndef COMPACT_OBSERVER
 push cs
 pop es
 mov si,SCREEN_ATTRIBUTE_CELLS
 mov di,flags
 mov cx,4096
 rep movsb
 mov si,ERASE_ATTRIBUTE_VALUES
 mov di,values
 mov cx,4096
 rep movsb
 mov bx,[ERASE_SHADOW_OFFSET]
 push ds
 mov ds,[ERASE_SHADOW_SEGMENT]
 mov si,bx
 mov di,shadow
 mov cx,8192
 rep movsb
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov di,video
 mov cx,2000
 rep movsw
 pop ds
%endif
 inc word [cs:exits]
.done:
 restore
 jmp far [cs:old21]
resident_end:
start:
 cmp byte [0x82],'T'
 jne collect
 mov ax,0x3510
 int 0x21
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [old21+2],es
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,handler10
 mov ax,0x2510
 int 0x21
 mov dx,handler21
 mov ax,0x2521
 int 0x21
 mov dx,handler1c
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 mov ax,0x3521
 int 0x21
 cmp bx,handler21
 jne failed
 cmp word [es:sample],0x5756
 jne failed
 mov ax,[es:old10]
 mov [old10],ax
 mov ax,[es:old10+2]
 mov [old10+2],ax
 mov ax,[es:old21]
 mov [old21],ax
 mov ax,[es:old21+2]
 mov [old21+2],ax
 mov ax,[es:old1c]
 mov [old1c],ax
 mov ax,[es:old1c+2]
 mov [old1c+2],ax
 pushf
 cli
 mov si,sample
 mov di,sample
 mov cx,sample_end-sample
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[old10]
 mov ax,[old10+2]
 push ds
 mov ds,ax
 mov ax,0x2510
 int 0x21
 pop ds
 mov dx,[old21]
 mov ax,[old21+2]
 push ds
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 mov dx,[old1c]
 mov ax,[old1c+2]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,sample
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,sample_end-sample
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\WVIEW.BIN',0
