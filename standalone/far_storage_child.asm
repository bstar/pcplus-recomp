; Synthetic PROGRAM child: locate owned parent through PSP chain, inspect its
; retained MCB extent, allocate/fill a separate DOS block, verify far canaries.
BITS 16
CPU 8086
ORG 0x100
%ifndef FAR_SEG
%error Linker-derived FAR_SEG required
%endif
%ifndef REQUIRED_PARAS
%error Linker-derived maximum REQUIRED_PARAS required
%endif
start:
 mov ax,cs
 cli
 mov ss,ax
 mov sp,child_stack_top
 sti
 mov ds,ax
 mov es,ax
 mov bx,(child_stack_top-$$+0x100+15)/16
 mov ah,0x4a
 int 0x21
 mov bx,[0x16]
 mov cx,8
.find:
 cmp bx,0x10
 jb .save
 mov ax,bx
 add ax,16+DGROUP_SEG
 mov es,ax
 cmp [es:PROCESS_PSP_OFFSET],bx
 jne .next
 mov ax,bx
 add ax,16+FAR_SEG
 cmp [es:SHADOW_SEGMENT_OFFSET],ax
 jne .next
 cmp [es:HISTORY_POINTER_OFFSET+2],ax
 jne .next
 mov [result+2],bx
 mov [result+8],ax
 or word [result],1
 dec bx
 mov es,bx
 mov ax,[es:3]
 mov [result+4],ax
 mov word [result+6],REQUIRED_PARAS
 cmp ax,REQUIRED_PARAS
 jb .save
 or word [result],2
 mov es,[result+8]
 mov word [es:SHADOW_OFFSET],0xcafe
 mov word [es:SHADOW_OFFSET+8190],0xbeef
 mov word [es:HISTORY_OFFSET],0xdead
 mov word [es:HISTORY_OFFSET+4094],0xbabe
 mov ax,[result+2]
 add ax,16+SNAPSHOT_SEG
 mov [result+20],ax
 mov es,ax
 mov word [es:SNAPSHOT_OFFSET],0x1122
 mov word [es:SNAPSHOT_OFFSET+1998],0x3344
 mov bx,0x400
 mov ah,0x48
 int 0x21
 jc .save
 mov [result+10],ax
 mov es,ax
 xor di,di
 mov ax,0x5353
 mov cx,0x2000
 cld
 rep stosw
 mov es,[result+8]
 mov ax,[es:SHADOW_OFFSET]
 mov [result+12],ax
 cmp ax,0xcafe
 jne .free
 mov ax,[es:SHADOW_OFFSET+8190]
 mov [result+14],ax
 cmp ax,0xbeef
 jne .free
 mov ax,[es:HISTORY_OFFSET]
 mov [result+16],ax
 cmp ax,0xdead
 jne .free
 mov ax,[es:HISTORY_OFFSET+4094]
 mov [result+18],ax
 cmp ax,0xbabe
 jne .free
 mov es,[result+20]
 mov ax,[es:SNAPSHOT_OFFSET]
 mov [result+22],ax
 cmp ax,0x1122
 jne .free
 mov ax,[es:SNAPSHOT_OFFSET+1998]
 mov [result+24],ax
 cmp ax,0x3344
 jne .free
 or word [result],4
.free:
 mov es,[result+10]
 mov ah,0x49
 int 0x21
 jmp .save
.next:
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,bx
 je .save
 mov bx,ax
 dec cx
 jz .save
 jmp .find
.save:
 mov dx,output
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .exit
 mov bx,ax
 mov dx,result
 mov cx,26
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.exit:
 mov ax,0x4c01
 cmp word [result],7
 jne .terminate
 xor al,al
.terminate:
 int 0x21
output: db 'D:\FARTEST.BIN',0
result: times 13 dw 0

align 2
 times 1024 db 0
child_stack_top:
