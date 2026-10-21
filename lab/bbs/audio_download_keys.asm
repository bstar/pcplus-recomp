; Test-only BIOS keys after an actual automatic ZMODEM receive. Observe video
; only; never touch product state, files, serial data or protocol replies.
bits 16
cpu 8086
org 100h
jmp install
%ifdef AUDIO_DOWNLOAD_FAST_TEST
%define MENU_WAIT 3
%define SEARCH_WAIT 3
%define KEY_WAIT 2
%define FINAL_WAIT 3
%else
%define MENU_WAIT 180
%define SEARCH_WAIT 90
%define KEY_WAIT 54
%define FINAL_WAIT 360
%endif
old_vector: dd 0
state: db 0
%ifdef AUDIO_DOWNLOAD_PRESSURE
watchdog: dw 54000 ; bounded before the3020s pressure outer deadline
%else
watchdog: dw 21240 ; bounded before the1200s outer deadline
%endif
ticks: dw 0
key_at: dw menu_keys
receiving: db 'Receiving ZMODEM',0
file_menu: db 'File Base',0
menu_footer: db '...cmd:',0
search_title: db 'FILE SEARCH',0
search_footer: db 'ESC : cancel',0
list_title: db 'QUEUED',0
%ifdef AUDIO_DOWNLOAD_PRESSURE
filename_marker: db 'PCPRESS.BIN',0
%else
filename_marker: db 'PCXTEST.BIN',0
%endif
menu_keys: dw 1f53h,1c0dh,0
%ifdef AUDIO_DOWNLOAD_PRESSURE
search_keys: dw 1950h,2e43h,1950h,1352h,1245h,1f53h,1f53h,342eh,3042h,1749h,314eh,1c0dh,1c0dh,0
%else
search_keys: dw 1950h,2e43h,2d58h,1454h,1245h,1f53h,1454h,342eh,3042h,1749h,314eh,1c0dh,1c0dh,0
%endif
exit_keys: dw 2d00h,0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 cld
 cmp byte [state],7
 je .done
 dec word [watchdog]
 jnz .watching
 mov cx,2d00h
 mov ah,5
 int 16h
 or al,al
 jz .restore
 inc word [watchdog]
 jmp .done
.watching:
 cmp byte [state],0
 jne .wait_menu
 mov si,receiving
 call visible
 jnc .done
 mov byte [state],1
 jmp .done
.wait_menu:
 cmp byte [state],1
 jne .wait_search
 mov si,receiving
 call visible
 jc .done
 mov si,file_menu
 call visible
 jnc .done
 mov si,menu_footer
 call visible
 jnc .done
 mov byte [state],2
 mov word [key_at],menu_keys
 mov word [ticks],MENU_WAIT
 jmp .done
.wait_search:
 cmp byte [state],3
 jne .wait_list
 mov si,search_title
 call visible
 jnc .done
 mov si,search_footer
 call visible
 jnc .done
 mov byte [state],4
 mov word [key_at],search_keys
 mov word [ticks],SEARCH_WAIT
 jmp .done
.wait_list:
 cmp byte [state],5
 jne .count
 mov si,list_title
 call visible
 jnc .done
 mov si,filename_marker
 call visible
 jnc .done
 mov byte [state],6
 mov word [key_at],exit_keys
 mov word [ticks],FINAL_WAIT
 jmp .done
.count:
 cmp byte [state],2
 je .active
 cmp byte [state],4
 je .active
 cmp byte [state],6
 jne .done
.active:
 dec word [ticks]
 jnz .done
 mov bx,[key_at]
 mov cx,[bx]
 mov ah,5
 int 16h
 or al,al
 jz .accepted
 inc word [ticks]
 jmp .done
.accepted:
 add word [key_at],2
 mov bx,[key_at]
 cmp word [bx],0
 je .phase_done
 mov word [ticks],KEY_WAIT
 cmp word [bx-2],1c0dh
 jne .done
 cmp word [bx],1c0dh
 jne .done
 mov word [ticks],SEARCH_WAIT
 jmp .done
.phase_done:
 cmp byte [state],6
 je .restore
 inc byte [state]
 jmp .done
.restore:
 mov byte [state],7
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[old_vector]
 mov [es:70h],ax
 mov ax,[old_vector+2]
 mov [es:72h],ax
 popf
.done:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
; Scan visible CP437 character cells only. CF1 means found; registers other
; than AX/DI/ES are preserved so two independent markers can be required.
visible:
 push si
 mov ax,0b800h
 mov es,ax
 xor di,di
.search:
 pop si
 push si
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp di,4000
 jae .miss
 cmp al,[es:di]
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,4000
 jb .search
 pop si
 clc
 ret
.found:
 pop di
 pop si
 stc
 ret
resident_end:
filename: db 'D:\KEYOLD.BIN',0
install:
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ah,3ch
 xor cx,cx
 mov dx,filename
 int 21h
 jc failure
 mov bx,ax
 mov ah,40h
 mov cx,4
 mov dx,old_vector
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc failure
 cmp ax,4
 jne failure
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
failure:
 mov ax,4c01h
 int 21h
