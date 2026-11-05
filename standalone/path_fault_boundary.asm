; Test-only, one-shot DOS boundary faults. No application memory/code writes.
; Foreground INT21 calls only; the timer observer is a separate passive helper.
BITS 16
CPU 8086
ORG 100h
jmp start
old21: dw 0,0
sample: dw 0x5046,0,0,0,0,0,0 ; magic,phase,OTHER/root successes,query/native faults,restored
pending: dw 0
%macro pop_inputs 0
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
%endmacro
handler:
 push bp
 mov bp,sp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 cmp ah,47h
 je query
 cmp ah,3bh
 jne chain
 mov si,dx
 ; Match the owned fixture leaf case-insensitively and exactly.
 mov ax,[si]
 or ax,2020h
 cmp ax,'ot'
 jne root_path
 mov ax,[si+2]
 or ax,2020h
 cmp ax,'he'
 jne chain
 mov al,[si+4]
 or al,20h
 cmp al,'r'
 jne chain
 cmp byte [si+5],0
 jne chain
 mov word [cs:pending],1
 jmp real_change
root_path:
 cmp byte [si],'D'
 jne chain
 cmp word [si+1],0x5c3a ; :\
 jne chain
 cmp byte [si+3],0
 jne chain
 cmp word [cs:sample+2],0
 je chain
%if PATH_FAULT_MODE = 2
 cmp word [cs:sample+2],2
 jne .allowed
%elif PATH_FAULT_MODE = 3
 cmp word [cs:sample+2],1
 jne .allowed
%else
 jmp .allowed
%endif
 mov word [cs:sample+2],3
 inc word [cs:sample+10]
 jmp denied
.allowed:
 mov word [cs:pending],2
real_change:
 pop_inputs
 pushf
 call far [cs:old21]
 jc .returned_error
 push ax
 cmp word [cs:pending],1
 jne .root
 cmp word [cs:sample+4],0
 jne .count_other
 mov word [cs:sample+2],1
.count_other:
 inc word [cs:sample+4]
 jmp .success
.root:
 mov word [cs:sample+2],4
 inc word [cs:sample+6]
.success:
 pop ax
 and word [ss:bp+6],0xfffe
 pop bp
 iret
.returned_error:
 or word [ss:bp+6],1
 pop bp
 iret
query:
 ; Modes1/2: first query after actual OTHER success. Mode4: query after
 ; actual root restoration. All earlier identity/resource calls pass through.
%if PATH_FAULT_MODE = 1 || PATH_FAULT_MODE = 2
 cmp word [cs:sample+2],1
 jne chain
 mov word [cs:sample+2],2
%elif PATH_FAULT_MODE = 4
 cmp word [cs:sample+2],4
 jne chain
 mov word [cs:sample+2],5
%else
 jmp chain
%endif
 inc word [cs:sample+8]
denied:
 pop_inputs
 mov ax,5
 or word [ss:bp+6],1
 pop bp
 iret
chain:
 pop_inputs
 pop bp
 jmp far [cs:old21]
resident_end:
start:
 mov ax,3521h
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old21],bx
 mov [old21+2],es
 mov dx,handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x5046
 jne failed
 mov si,sample
 mov di,report
 mov cx,14
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old21]
 mov [expected_off],dx
 mov ax,[es:old21+2]
 mov [expected_seg],ax
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[expected_off]
 jne failed
 mov ax,es
 cmp ax,[expected_seg]
 jne failed
 mov word [report+12],1
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,report
 mov cx,14
 mov ah,40h
 int 21h
 jc failed
 cmp ax,14
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\PATHFLT.BIN',0
expected_off: dw 0
expected_seg: dw 0
report: times 14 db 0
