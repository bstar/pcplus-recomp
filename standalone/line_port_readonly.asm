; Diagnostic only: brackets a DOS read-only attribute on the authored PRM.
BITS 16
CPU 8086
ORG 100h
 xor cx,cx
 cmp byte [82h],'T'
 jne .set
 mov cx,1
.set:
 mov dx,path
 mov ax,4301h
 int 21h
 jc .failed
 mov ax,4c00h
 int 21h
.failed:
 mov ax,4c01h
 int 21h
path: db 'D:\TEST.PRM',0
