; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_spawnv
extern program_spawn_extension
extern program_access
extern program_strcpy
extern program_strlen
extern program_strchr
extern program_strrchr
extern program_strcmpi
extern program_service_92a8
extern program_service_92a4
extern program_service_93ca
extern program_pair_low
extern program_extensions
extern program_extension2
extern program_heap_mode
%define short
%else
ORG 0x68ee
%define program_spawn_extension 0x684a
%define program_access 0x93aa
%define program_strcpy 0x8268
%define program_strlen 0x8d18
%define program_strchr 0x8c2a
%define program_strrchr 0x83c6
%define program_strcmpi 0x93de
%define program_service_92a8 0x92a8
%define program_service_92a4 0x92a4
%define program_service_93ca 0x93ca
%define program_pair_low 0x2e
%define program_extensions 0x5e30
%define program_extension2 0x5e34
%define program_heap_mode 0x7b54
%endif
%include "encodings.inc"
program_spawnv:
L_68ee: push bp
L_68ef: mov_load bp,sp
L_68f1: sub sp,0xa
L_68f4: push di
L_68f5: push si
L_68f6: cmp word [bp+0x4],0x2
L_68fa: jnz short L_690e
L_68fc: push word [bp+0xa]
L_68ff: push word [bp+0x8]
L_6902: push word [bp+0x6]
L_6905: call program_service_93ca
L_6908: add sp,0x6
L_690b: jmp near L_6a11
L_690e: mov ax,0x5c
L_6911: push ax
L_6912: push word [bp+0x6]
L_6915: call program_strrchr
L_6918: pop bx
L_6919: pop bx
L_691a: mov_load si,ax
L_691c: mov ax,0x2f
L_691f: push ax
L_6920: push word [bp+0x6]
L_6923: call program_strrchr
L_6926: pop bx
L_6927: pop bx
L_6928: mov_load di,ax
L_692a: or_load di,di
L_692c: jnz short L_6937
L_692e: or_load si,si
L_6930: jnz short L_6941
L_6932: mov si,[bp+0x6]
L_6935: jmp short L_6941
L_6937: or_load si,si
L_6939: jz short L_693f
L_693b: cmp_load di,si
L_693d: jna short L_6941
L_693f: mov_load si,di
L_6941: mov ax,0x2e
L_6944: push ax
L_6945: push si
L_6946: call program_strchr
L_6949: pop bx
L_694a: pop bx
L_694b: mov_load di,ax
L_694d: or_load di,di
L_694f: jz short L_6973
L_6951: push word [program_extensions]
L_6955: push di
L_6956: call program_strcmpi
L_6959: pop bx
L_695a: pop bx
L_695b: push ax
L_695c: push word [bp+0xa]
L_695f: push word [bp+0x8]
L_6962: push word [bp+0x6]
L_6965: push word [bp+0x4]
L_6968: call program_spawn_extension
L_696b: add sp,0xa
L_696e: mov_load si,ax
L_6970: jmp near L_6a0f
L_6973: mov si,[program_heap_mode]
L_6977: mov word [program_heap_mode],0x10
L_697d: push word [bp+0x6]
L_6980: call program_strlen
L_6983: pop bx
L_6984: add ax,strict word 0x5
L_6987: push ax
L_6988: call program_service_92a8
L_698b: pop bx
L_698c: mov_load di,ax
L_698e: mov [program_heap_mode],si
L_6992: or_load di,di
L_6994: jnz short L_699b
L_6996: mov ax,0xffff
L_6999: jmp short L_6a11
L_699b: push word [bp+0x6]
L_699e: push di
L_699f: call program_strcpy
L_69a2: pop bx
L_69a3: pop bx
L_69a4: push word [bp+0x6]
L_69a7: call program_strlen
L_69aa: pop bx
L_69ab: add_load ax,di
L_69ad: mov [bp-0x6],ax
L_69b0: mov word [bp-0xa],0xffff
L_69b5: mov word [bp-0x4],0x2
L_69ba: mov word [bp-0x2],program_extension2
L_69bf: mov [bp-0x8],di
L_69c2: jmp short L_69e6
L_69c4: mov bx,[bp-0x2]
L_69c7: push word [bx]
L_69c9: push word [bp-0x6]
L_69cc: call program_strcpy
L_69cf: pop bx
L_69d0: pop bx
L_69d1: sub_load ax,ax
L_69d3: push ax
L_69d4: push word [bp-0x8]
L_69d7: call program_access
L_69da: pop bx
L_69db: pop bx
L_69dc: inc ax
L_69dd: jnz short L_69f1
L_69df: sub word [bp-0x2],0x2
L_69e3: dec word [bp-0x4]
L_69e6: cmp word [bp-0x4],0x0
L_69ea: jnl short L_69c4
L_69ec: mov si,[bp-0xa]
L_69ef: jmp short L_6a08
L_69f1: push word [bp-0x4]
L_69f4: push word [bp+0xa]
L_69f7: push word [bp+0x8]
L_69fa: push word [bp-0x8]
L_69fd: push word [bp+0x4]
L_6a00: call program_spawn_extension
L_6a03: add sp,0xa
L_6a06: mov_load si,ax
L_6a08: push word [bp-0x8]
L_6a0b: call program_service_92a4
L_6a0e: pop bx
L_6a0f: mov_load ax,si
L_6a11: pop si
L_6a12: pop di
L_6a13: mov_load sp,bp
L_6a15: pop bp
L_6a16: ret
