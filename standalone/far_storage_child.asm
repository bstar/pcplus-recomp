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
 mov dx,ax
 mov ax,bx
 add ax,16+HISTORY_SEG
 cmp [es:HISTORY_POINTER_OFFSET+2],ax
 jne .next
 mov [result+2],bx
 mov [result+8],dx
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
 mov ax,[result+2]
 add ax,16+HISTORY_SEG
 mov es,ax
 mov word [es:HISTORY_OFFSET],0xdead
 mov word [es:HISTORY_OFFSET+62998],0xbabe
 mov ax,[result+2]
 add ax,16+SNAPSHOT_SEG
 mov [result+20],ax
 mov es,ax
 mov word [es:SNAPSHOT_OFFSET],0x1122
 mov word [es:SNAPSHOT_OFFSET+1998],0x3344
 mov ax,[result+2]
 add ax,16+CODE_SEG
 mov es,ax
 mov [result+30],ax
 mov word [result+32],CODE_BYTES
 cmp word [es:CODE_START],CODE_FIRST
 jne .save
 call code_sum
 mov [result+26],ax
 mov ax,[result+2]
 add ax,16+MODEM_SEG
 mov es,ax
 mov [result+48],ax
 mov word [result+50],MODEM_BYTES
 call modem_sum
 mov [result+52],ax
 mov ax,[result+2]
 add ax,16+CONFIG_SEG
 mov es,ax
 mov [result+56],ax
 mov word [result+58],CONFIG_BYTES
 call config_sum
 mov [result+60],ax
 mov ax,[result+2]
 add ax,16+UI_SEG
 mov es,ax
 mov [result+34],ax
 mov si,BROWSER_OFF
 call ui_sum
 mov [result+36],ax
 mov si,EDITOR_OFF
 call ui_sum
 mov [result+40],ax
 mov si,PROGRAM_OFF
 call ui_sum
 mov [result+44],ax
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
 mov ax,[result+2]
 add ax,16+HISTORY_SEG
 mov es,ax
 mov ax,[es:HISTORY_OFFSET]
 mov [result+16],ax
 cmp ax,0xdead
 jne .free
 mov ax,[es:HISTORY_OFFSET+62998]
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
 mov es,[result+30]
 call code_sum
 mov [result+28],ax
 cmp ax,[result+26]
 jne .free
 or word [result],8
 mov es,[result+48]
 call modem_sum
 mov [result+54],ax
 cmp ax,[result+52]
 jne .free
 or word [result],32
 mov es,[result+56]
 call config_sum
 mov [result+62],ax
 cmp ax,[result+60]
 jne .free
 or word [result],64
 mov es,[result+34]
 mov si,BROWSER_OFF
 call ui_sum
 mov [result+38],ax
 cmp ax,[result+36]
 jne .free
 mov si,EDITOR_OFF
 call ui_sum
 mov [result+42],ax
 cmp ax,[result+40]
 jne .free
 mov si,PROGRAM_OFF
 call ui_sum
 mov [result+46],ax
 cmp ax,[result+44]
 jne .free
 or word [result],16
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
 mov cx,64
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.exit:
 mov ax,0x4c01
 cmp word [result],127
 jne .terminate
 xor al,al
.terminate:
 int 0x21
; Byte sum includes every relocated far-code byte; independent before/after
; samples establish that child allocation did not reuse the parent code extent.
code_sum:
 mov si,CODE_START
 mov cx,CODE_BYTES
 jmp sum_bytes
modem_sum:
 mov si,MODEM_START
 mov cx,MODEM_BYTES
 jmp sum_bytes
config_sum:
 mov si,CONFIG_START
 mov cx,CONFIG_BYTES
 jmp sum_bytes
ui_sum:
 mov cx,4000
sum_bytes:
 xor bx,bx
.loop:
 xor ax,ax
 mov al,[es:si]
 add bx,ax
 inc si
 loop .loop
 mov ax,bx
 ret
output: db 'D:\FARTEST.BIN',0
result: times 32 dw 0

align 2
 times 1024 db 0
child_stack_top:
