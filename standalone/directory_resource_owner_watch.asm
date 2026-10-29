; Test-only passive DOS/INT1C observer. No keyboard/UART writes, product hooks,
; fake returns. Runtime data offsets come from map. CORRUPT_PROPOSAL enables
; one declared test-only RAM fault at the actual mouse-suspend boundary.
BITS 16
CPU 8086
ORG 100h
%include "owner-watch.inc"
%define CAPTURE_SIZE (14+2*FIELD_BYTES+1190+2*1624+14+142+4000+14)
jmp start
old_tick: dw 0,0
old_dos: dw 0,0
old_irq: dw 0,0
%ifdef CORRUPT_PROPOSAL
old_mouse: dw 0,0
%endif
sample: dw 0x524f,0,0,0,0,0,0
before_fields: times FIELD_BYTES db 0
after_fields: times FIELD_BYTES db 0
proposal: times 1190 db 0
before_bundle: times 1624 db 0
after_bundle: times 1624 db 0
owner_state: times 14 db 0
resource_state: times 142 db 0
prompt_frame: times 4000 db 0
released_owner: times 14 db 0
parent_irq: dw 0,0
parent_ier: db 0
parent_mcr: db 0
parent_pic: db 0
directory_name: db 'PCPLUS.DIR',0
prompt_text: db 'Press any key.',0
%ifdef CORRUPT_PROPOSAL
mouse_handler:
 pushf
 push ax
 push es
 test word [cs:sample+2],8
 jnz .done
 mov ax,[cs:sample+12]
 or ax,ax
 jz .done
 mov es,ax
 cmp word [es:OWNER],1
 jne .done
 cmp word [es:PROGRAM_PENDING],1
 jne .done
 cmp word [es:PROGRAM_KIND],6
 jne .done
 add ax,FROZEN_RELATIVE
 mov es,ax
 xor byte [es:FROZEN_OFFSET+2788],1
 or word [cs:sample+2],8
.done:
 pop es
 pop ax
 popf
 jmp far [cs:old_mouse]
%endif
dos_handler:
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
 mov bx,ds
 cmp word [cs:sample+12],0
 jne .known
 cmp ah,3dh
 jne .done
 mov si,dx
 mov di,directory_name
 mov cx,11
.name:
 lodsb
 cmp al,[cs:di]
 jne .done
 inc di
 loop .name
 mov [cs:sample+12],bx
.known:
 cmp bx,[cs:sample+12]
 jne .done
 cmp word [OWNER],2 ; RUNNING: inspect every actual DOS boundary in this owner.
 jne .done
 inc word [cs:sample+6]
 cmp ah,3dh
 jne .gates
 inc word [cs:sample+8]
 cmp al,80h
 jne .bad
.gates:
 mov bx,ss
 mov dx,ds
 cmp bx,dx
 jne .bad
 cmp word [PROGRAM_PENDING],0
 jne .bad
 cmp word [PROGRAM_ACTIVE],1
 jne .bad
 cmp word [PROGRAM_KIND],6
 jne .bad
 cmp word [PROGRAM_STATUS],2
 jne .bad
 mov ax,[REDISPLAY_ACTIVE]
 or ax,[COMMAND_ACTIVE]
 or ax,[CONNECTION]
 jnz .bad
 mov dx,3e9h
 in al,dx
 or al,al
 jnz .bad
 mov dx,3ech
 in al,dx
 test al,2
 jnz .bad
 in al,21h
 test al,20h
 jz .bad
 xor ax,ax
 mov es,ax
 mov ax,[es:34h]
 cmp ax,[cs:old_irq]
 jne .bad
 mov ax,[es:36h]
 cmp ax,[cs:old_irq+2]
 je .done
.bad:
 inc word [cs:sample+10]
.done:
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
 jmp far [cs:old_dos]
tick_handler:
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
 inc word [cs:sample+4]
 mov ax,[cs:sample+12]
 or ax,ax
 jz .done
 mov ds,ax
 test word [cs:sample+2],1
 jnz .after
 cmp word [REDISPLAY_ACTIVE],1
 jne .done
 cmp word [COMMAND_ACTIVE],1
 jne .done
 mov ax,0b800h
 mov es,ax
 cmp word [es:484],1f53h ; SELECTED ENTRY, complete preview footer starts R.
 jne .done
 cmp word [es:3842],1f52h
 jne .done
 mov dx,3e9h
 in al,dx
 mov [cs:parent_ier],al
 mov dx,3ech
 in al,dx
 mov [cs:parent_mcr],al
 in al,21h
 and al,20h
 mov [cs:parent_pic],al
 xor ax,ax
 mov es,ax
 mov ax,[es:34h]
 mov [cs:parent_irq],ax
 mov ax,[es:36h]
 mov [cs:parent_irq+2],ax
 push cs
 pop es
 mov di,before_fields
 call fields
 mov ax,ds
 add ax,FROZEN_RELATIVE
 mov ds,ax
 mov si,FROZEN_OFFSET+2788
 mov di,proposal
 mov cx,1190
 rep movsb
 mov si,FROZEN_OFFSET+3978
 mov di,before_bundle
 mov cx,1624
 rep movsb
 or word [cs:sample+2],1
 jmp .done
.after:
 test word [cs:sample+2],2
 jnz .released
 cmp word [PROGRAM_ACTIVE],1
 jne .done
 cmp word [PROGRAM_KIND],6
 jne .done
 cmp word [PROGRAM_STATUS],4
 je .ready
 cmp word [PROGRAM_STATUS],5
 jne .done
.ready:
 cmp word [OWNER],3
 je .notice
 cmp word [OWNER],4
 jne .done
.notice:
 mov ax,0b800h
 mov es,ax
 xor bx,bx
.scan:
 cmp bx,3974
 ja .done
 mov si,bx
 mov di,prompt_text
.match:
 mov al,[cs:di]
 or al,al
 jz .capture
 cmp al,[es:si]
 jne .next
 add si,2
 inc di
 jmp .match
.next:
 add bx,2
 jmp .scan
.capture:
 push cs
 pop es
 mov di,after_fields
 call fields
 mov si,OWNER
 mov di,owner_state
 mov cx,14
 rep movsb
 mov si,RESOURCE
 mov di,resource_state
 mov cx,142
 rep movsb
 mov ax,ds
 add ax,FROZEN_RELATIVE
 mov ds,ax
 mov si,FROZEN_OFFSET+3978
 mov di,after_bundle
 mov cx,1624
 rep movsb
 mov ax,0b800h
 mov ds,ax
 xor si,si
 mov di,prompt_frame
 mov cx,4000
 rep movsb
 or word [cs:sample+2],2
 jmp .done
.released:
 test word [cs:sample+2],4
 jnz .done
 mov ax,[PROGRAM_PENDING]
 or ax,[PROGRAM_ACTIVE]
 or ax,[REDISPLAY_ACTIVE]
 or ax,[COMMAND_ACTIVE]
 or ax,[OWNER]
 jnz .done
 cmp word [OWNER+12],1
 jne .done
 mov dx,3e9h
 in al,dx
 cmp al,[cs:parent_ier]
 jne .restore_bad
 mov dx,3ech
 in al,dx
 cmp al,[cs:parent_mcr]
 jne .restore_bad
 in al,21h
 and al,20h
 cmp al,[cs:parent_pic]
 jne .restore_bad
 xor ax,ax
 mov es,ax
 mov ax,[es:34h]
 cmp ax,[cs:parent_irq]
 jne .restore_bad
 mov ax,[es:36h]
 cmp ax,[cs:parent_irq+2]
 je .restored
.restore_bad:
 inc word [cs:sample+10]
.restored:
 push cs
 pop es
 mov si,OWNER
 mov di,released_owner
 mov cx,14
 rep movsb
 or word [cs:sample+2],4
.done:
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
 jmp far [cs:old_tick]
fields:
 mov bp,field_table
 mov bx,FIELD_COUNT
.copy:
 mov si,[cs:bp]
 mov cx,[cs:bp+2]
 rep movsb
 add bp,4
 dec bx
 jnz .copy
 ret
field_table:
%include "owner-fields.inc"
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_tick],bx
 mov [old_tick+2],es
 mov ax,3521h
 int 21h
 mov [old_dos],bx
 mov [old_dos+2],es
 mov ax,350dh
 int 21h
 mov [old_irq],bx
 mov [old_irq+2],es
%ifdef CORRUPT_PROPOSAL
 mov ax,3533h
 int 21h
 mov [old_mouse],bx
 mov [old_mouse+2],es
 mov dx,mouse_handler
 mov ax,2533h
 int 21h
%endif
 mov dx,dos_handler
 mov ax,2521h
 int 21h
 mov dx,tick_handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,tick_handler
 jne failed
 cmp word [es:sample],524fh
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,CAPTURE_SIZE
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
%ifdef CORRUPT_PROPOSAL
 mov dx,[es:old_mouse]
 mov ax,[es:old_mouse+2]
 push ds
 mov ds,ax
 mov ax,2533h
 int 21h
 pop ds
%endif
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov dx,[es:old_tick]
 mov ax,[es:old_tick+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,CAPTURE_SIZE
 mov ah,40h
 int 21h
 jc failed
 cmp ax,CAPTURE_SIZE
 jne failed
 mov ah,3eh
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'OWNER.BIN',0
buffer: times CAPTURE_SIZE db 0
