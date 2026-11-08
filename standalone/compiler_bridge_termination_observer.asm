; Owned negative-test TSR, never linked into the application. No parent tail
; or freed child data is read after termination. All DOS instrumentation calls
; chain directly to old21; the report is written only after observed fail-stop.
BITS 16
CPU 8086
ORG 100h
jmp start
old21: dd 0
old10: dd 0
old1c: dd 0
indos: dd 0
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
report:
 dw 0x5446,2
parent_psp: dw 0
parent_ds: dw 0
child_psp: dw 0
child_ds: dw 0
child_paras: dw 0
aspect_execs: dw 0
compiler_execs: dw 0
compiler_exits: dw 0
compiler_code: dw 0xffff
killed: dw 0
injection_point: dw TERMINATION_POINT
kill_ss: dw 0
kill_extent: dw 0
restore_reads: dw 0
restore_position: dw 0
aspect_exits: dw 0
aspect_code: dw 0xffff
guard_seen: dw 0
guard_ticks: dw 0
ier: dw 0xffff
irq_offset: dw 0
irq_segment: dw 0
current_psp: dw 0
parent_extent: dw 0
parent_owner: dw 0
post_dos: dw 0
post_resizes: dw 0
post_reads: dw 0
post_writes: dw 0
outside_retained: dw 0
text_count: dw 0
video_other: dw 0
video_overflow: dw 0
before_attrs: dw 0
after_attrs: dw 0
before_row: dw 0
before_col: dw 0
after_row: dw 0
after_col: dw 0
before_history: times 2 dw 0
after_history: times 2 dw 0
write_error: dw 0
observer_segment: dw 0
kernel_before: times 14 dw 0
kernel_after: times 14 dw 0
text: times 128 db 0
video: times 4000 db 0
report_end:
dumped: dw 0
tmp_name: db 'D:\FATAL.TMP',0
report_name: db 'D:\FATAL.BIN',0
aspect_name: db 'C:\ASPECT.EXE',0
compiler_name: db 'C:\ASPCOMP.EXE',0
notice: db 'Parent memory restore incomplete.'

; BP addresses the outer save frame: AX16, IP20, CS22, FLAGS24.
handler:
 save
 cld
 mov bp,sp
 cmp word [cs:parent_psp],0
 je .exec
 cmp word [cs:aspect_exits],1
 jne .exec
 mov ax,[cs:parent_psp]
 add ax,16
 cmp [ss:bp+22],ax
 jb .exec
 mov dx,ax
 add ax,FULL_PARAS-16
 cmp [ss:bp+22],ax
 jae .exec
 inc word [cs:post_dos]
 mov ax,dx
 add ax,KEEP_PARAS-16
 cmp [ss:bp+22],ax
 jb .retained
 inc word [cs:outside_retained]
.retained:
 cmp byte [ss:bp+17],0x4a
 jne .read
 inc word [cs:post_resizes]
.read:
 cmp byte [ss:bp+17],0x3f
 jne .write
 inc word [cs:post_reads]
.write:
 cmp byte [ss:bp+17],0x40
 jne .exec
 inc word [cs:post_writes]
.exec:
 cmp word [ss:bp+16],0x4b00
 jne .exit
 mov si,[ss:bp+10]
 mov di,aspect_name
 call same_name
 or ax,ax
 jz .compiler
 cmp word [cs:aspect_execs],0
 jne .chain
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .chain
 mov [cs:parent_ds],ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 cmp bx,[PROCESS_PSP]
 jne .chain
 mov es,bx
 cmp word [es:0],0x20cd
 jne .chain
 mov [cs:parent_psp],bx
 inc word [cs:aspect_execs]
 jmp .chain
.compiler:
 mov si,[ss:bp+10]
 mov di,compiler_name
 call same_name
 or ax,ax
 jz .chain
 cmp word [cs:aspect_execs],1
 jne .chain
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .chain
 mov [cs:child_ds],ax
 sub ax,CHILD_GROUP+16
 mov dx,ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 cmp bx,dx
 jne .chain
 mov es,bx
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .chain
 mov [cs:child_psp],bx
 inc word [cs:compiler_execs]
 jmp .chain
.exit:
 cmp byte [ss:bp+17],0x4c
 jne .status
 cmp word [cs:compiler_execs],1
 jne .chain
 mov ah,0x51
 pushf
 call far [cs:old21]
 cmp bx,[cs:child_psp]
 jne .compiler_exit
 inc word [cs:aspect_exits]
 mov al,[ss:bp+16]
 xor ah,ah
 mov [cs:aspect_code],ax
 jmp .chain
.compiler_exit:
 mov es,bx
 mov ax,[cs:child_psp]
 cmp [es:0x16],ax
 jne .chain
 inc word [cs:compiler_exits]
 mov al,[ss:bp+16]
 xor ah,ah
 mov [cs:compiler_code],ax
 jmp .chain
.status:
%if TERMINATION_POINT == 1
 cmp byte [ss:bp+17],0x4d
%else
 cmp byte [ss:bp+17],0x3f
%endif
 jne .chain
 cmp word [cs:compiler_exits],1
 jne .chain
 cmp word [cs:killed],0
 jne .chain
 mov ax,ss
%if TERMINATION_POINT == 1
 cmp ax,[cs:child_ds]
%else
 cmp ax,[cs:parent_ds]
%endif
 jne .chain
 mov ah,0x51
 pushf
 call far [cs:old21]
 cmp bx,[cs:child_psp]
 jne .chain
 call kernel_segment
 cmp word [es:KERNEL_OFFSET],0x434c
 jne .chain
%if TERMINATION_POINT == 1
 cmp word [es:KERNEL_OFFSET+12],2
%else
 cmp word [es:KERNEL_OFFSET+12],3
%endif
 jne .chain
 cmp word [es:KERNEL_OFFSET+22],0
 jne .chain
%if TERMINATION_POINT == 2
 mov ax,[es:KERNEL_OFFSET+14]
 cmp [ss:bp+14],ax
 jne .chain
 cmp word [ss:bp+10],0
 jne .chain
 cmp word [ss:bp+12],4096
 jne .chain
 mov ax,[cs:parent_psp]
 add ax,KEEP_PARAS
 cmp word [cs:restore_reads],0
 jne .second_read
 cmp [ss:bp+2],ax
 jne .chain
 inc word [cs:restore_reads]
 jmp .chain ; Actual first block is restored by DOS/kernel, not this fixture.
.second_read:
 cmp word [cs:restore_reads],1
 jne .chain
 add ax,256
 cmp [ss:bp+2],ax
 jne .chain
 inc word [cs:restore_reads]
 mov bx,[ss:bp+14]
 xor cx,cx
 xor dx,dx
 mov ax,0x4201
 pushf
 call far [cs:old21]
 jc .chain
 or dx,dx
 jnz .chain
 cmp ax,4096
 jne .chain
 mov [cs:restore_position],ax
%endif
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
%if TERMINATION_POINT == 1
 cmp word [es:3],KEEP_PARAS
%else
 cmp word [es:3],FULL_PARAS
%endif
 jne .chain
 mov ax,[es:3]
 mov [cs:kill_extent],ax
 mov ax,ss
 mov [cs:kill_ss],ax
 mov ax,[cs:child_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:child_paras],ax
 mov di,kernel_before
 call copy_kernel
 mov di,before_attrs
 call copy_model
 mov word [cs:killed],1
 mov word [ss:bp+20],terminate_child
 mov [ss:bp+22],cs
 restore
 iret
.chain:
 restore
 jmp far [cs:old21]

terminate_child:
 mov ax,0x4c55
 int 0x21 ; Real termination of CurrentPDB=ASPECT, not a fabricated EXEC return.
 cli
.bad: hlt
 jmp .bad

same_name:
 mov cx,64
.next:
 mov al,[si]
 cmp al,[cs:di]
 jne .no
 inc si
 inc di
 or al,al
 jz .yes
 loop .next
.no: xor ax,ax
 ret
.yes: mov ax,1
 ret
kernel_segment:
 mov ax,[cs:parent_psp]
 add ax,16+KERNEL_SEGMENT
 mov es,ax
 ret
copy_kernel:
 call kernel_segment
 mov si,KERNEL_OFFSET
 mov cx,14
.next:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .next
 ret
; Only retained near attributes, cursor and the VALUES of history pointers.
; Never follow a history pointer or sample the freed interpreter allocation.
copy_model:
 mov es,[cs:parent_ds]
 mov si,ATTRS
 mov cx,2000
 mov dx,0xffff
.byte:
 xor dl,[es:si]
 inc si
 mov bl,8
.bit:
 shr dx,1
 jnc .plain
 xor dx,0xa001
.plain:
 dec bl
 jnz .bit
 loop .byte
 mov [cs:di],dx
 cmp di,before_attrs
 je .before
 mov di,after_row
 jmp .values
.before:
 mov di,before_row
.values:
 mov ax,[es:ROW]
 mov [cs:di],ax
 mov ax,[es:COL]
 mov [cs:di+2],ax
 cmp di,before_row
 jne .after_history
 mov di,before_history
 jmp .history
.after_history: mov di,after_history
.history:
 mov ax,[es:HISTORY]
 mov [cs:di],ax
 mov ax,[es:HISTORY+2]
 mov [cs:di+2],ax
 ret

video_handler:
 save
 mov bp,sp
 cmp word [cs:killed],1
 jne .done
 cmp byte [ss:bp+17],0x0e
 je .text
 inc word [cs:video_other]
 jmp .done
.text:
 mov bx,[cs:text_count]
 cmp bx,128
 jb .room
 mov word [cs:video_overflow],1
 jmp .done
.room:
 mov al,[ss:bp+16]
 mov [cs:text+bx],al
 inc word [cs:text_count]
.done:
 restore
 jmp far [cs:old10]

timer:
 save
 cld
 cmp word [cs:dumped],0
 jne .done
 cmp word [cs:killed],1
 jne .done
 cmp word [cs:aspect_exits],1
 jne .done
 les bx,[cs:indos]
 cmp byte [es:bx],0
 jne .done
 cmp word [cs:text_count],FATAL_LENGTH
 jne .done
 mov ax,0xb800
 mov es,ax
 xor bx,bx
.scan:
 mov di,bx
 mov si,notice
 mov cx,33
.compare:
 mov al,[es:di]
 cmp al,[cs:si]
 jne .next
 inc si
 add di,2
 loop .compare
 jmp .found
.next:
 add bx,2
 cmp bx,3934
 jbe .scan
 jmp .done
.found:
 mov word [cs:guard_seen],1
 inc word [cs:guard_ticks]
 cmp word [cs:guard_ticks],5
 jb .done
 mov ax,cs
 mov [cs:observer_segment],ax
 mov ah,0x51
 pushf
 call far [cs:old21]
 mov [cs:current_psp],bx
 mov ax,[cs:parent_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:parent_extent],ax
 mov ax,[es:1]
 mov [cs:parent_owner],ax
 mov di,kernel_after
 call copy_kernel
 mov di,after_attrs
 call copy_model
 mov es,[cs:parent_ds]
 mov dx,[es:IER_PORT]
 xor ax,ax
 in al,dx
 mov [cs:ier],ax
 mov bx,[es:IRQ_VECTOR]
 shl bx,1
 shl bx,1
 xor ax,ax
 mov es,ax
 mov ax,[es:bx]
 mov [cs:irq_offset],ax
 mov ax,[es:bx+2]
 mov [cs:irq_segment],ax
 push cs
 pop es
 mov di,video
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov cx,2000
 rep movsw
 push cs
 pop ds
 mov dx,tmp_name
 xor cx,cx
 mov ah,0x3c
 pushf
 call far [cs:old21]
 jc .write_failed
 mov bx,ax
 mov dx,report
 mov cx,report_end-report
 mov ah,0x40
 pushf
 call far [cs:old21]
 jc .close_failed
 cmp ax,report_end-report
 jne .close_failed
 mov ah,0x3e
 pushf
 call far [cs:old21]
 jc .write_failed
 push cs
 pop es
 mov dx,tmp_name
 mov di,report_name
 mov ah,0x56
 pushf
 call far [cs:old21]
 jc .write_failed
 mov word [cs:dumped],1
 jmp .done
.close_failed:
 mov ah,0x3e
 pushf
 call far [cs:old21]
.write_failed:
 mov word [cs:write_error],1
.done:
 restore
 jmp far [cs:old1c]
resident_end:
start:
 mov ax,[0x2c]
 or ax,ax
 jz .vectors
 mov es,ax
 mov ah,0x49
 int 0x21
 jc .failed
 mov word [0x2c],0
.vectors:
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [old21+2],es
 mov ah,0x34
 int 0x21
 mov [indos],bx
 mov [indos+2],es
 mov ax,0x3510
 int 0x21
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,handler
 mov ax,0x2521
 int 0x21
 mov dx,video_handler
 mov ax,0x2510
 int 0x21
 mov dx,timer
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
