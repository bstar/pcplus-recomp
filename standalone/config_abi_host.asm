; Actual near-C configuration calls from an assembly-owned DOS entry/stack.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
extern _prm_dos_load,_prm_dos_save,_prm_dos_replace
; Open Watcom model-consistency marker. No C startup/stdio is invoked here.
global _small_code_
_small_code_:
..start:
 mov ax,DGROUP
 mov ds,ax
 mov es,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
%macro pointer 1
 mov ax,%1
 push ax
%endmacro
 ; A small enum would leave AH unspecified. Every comparison checks full AX.
 pointer result
 pointer image
 xor ax,ax
 push ax
 mov bp,0xbabe
 mov si,0x1234
 mov di,0x5678
 call _prm_dos_load
 add sp,6
 cmp ax,1
 jne bad
 cmp bp,0xbabe
 jne bad
 cmp si,0x1234
 jne bad
 cmp di,0x5678
 jne bad
 pointer result
 pointer loaded
 pointer missing
 call _prm_dos_load
 add sp,6
 cmp ax,2
 jne bad
 cmp word [result+2],2
 jne bad
 cmp byte [loaded],0xcc
 jne bad
 pointer result
 pointer image
 xor ax,ax
 push ax
 call _prm_dos_save
 add sp,6
 cmp ax,1
 jne bad
 pointer result
 pointer image
 pointer no_directory
 call _prm_dos_save
 add sp,6
 cmp ax,2
 jne bad
 pointer replacement
 xor ax,ax
 push ax
 pointer backup
 pointer stage
 pointer target
 call _prm_dos_replace
 add sp,10
 cmp ax,1
 jne bad
 pointer result
 pointer image
 pointer output
 call _prm_dos_save
 add sp,6
 or ax,ax
 jnz bad
 pointer result
 pointer loaded
 pointer output
 call _prm_dos_load
 add sp,6
 or ax,ax
 jnz bad
 mov si,image
 mov di,loaded
 mov cx,1264
 repe cmpsb
 jne bad
 cmp sp,stack_top
 jne bad
 mov ax,0x4c00
 int 0x21
bad:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
 db 0 ; Offset zero is a NULL near pointer to C.
missing: db 'MISSING.PRM',0
no_directory: db 'NO_DIR\BAD.PRM',0
output: db 'ABI.PRM',0
target: db 'TARGET.PRM',0
stage: db 'STAGE.TMP',0
backup: db 'BACKUP.BAK',0
image: times 1264 db 0xa5
loaded: times 1264 db 0xcc
result: times 8 db 0
replacement: times 18 db 0
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
 resb 8192
stack_top:
