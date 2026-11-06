; Owned DOS COM argv/CWD probe for the original external-viewer route.
bits 16
cpu 8086
org 100h
jmp start
report:
 dw 5645h,1,0,0
tail times 128 db 0
drive dw 0
current_path times 64 db 0
report_end:
start:
 push cs
 pop ds
 push cs
 pop es
 mov ax,cs
 mov [report+4],ax
 mov si,80h
 mov di,tail
 mov cx,128
 cld
 rep movsb
 mov ah,19h
 int 21h
 xor ah,ah
 mov [drive],ax
 xor dl,dl
 mov si,current_path
 mov ah,47h
 int 21h
 jc failed
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,report
 mov cx,report_end-report
 mov ah,40h
 int 21h
 jc failed
 cmp ax,report_end-report
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
name db 'D:\VCHILD.BIN',0
