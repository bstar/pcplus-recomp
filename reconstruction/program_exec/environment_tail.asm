; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_environment_tail
extern program_get_ds
extern program_strcpy
extern program_strlen
extern program_strchr
extern program_service_92a8
extern program_service_860f
extern program_service_9286
extern program_service_92a4
extern program_environ
extern program_errno
extern program_dos_error
extern program_batch_prefix
extern program_fallback_environment
extern program_heap_mode
extern program_state_7b52
extern program_state_7b29
extern program_state_7b2a
extern program_state_e462
extern program_state_e45e
extern program_state_e460
extern program_state_7b2b
extern program_state_7b00
%define short
%else
ORG 0x65ca
%define program_get_ds 0x76b0
%define program_strcpy 0x8268
%define program_strlen 0x8d18
%define program_strchr 0x8c2a
%define program_service_92a8 0x92a8
%define program_service_860f 0x860f
%define program_service_9286 0x9286
%define program_service_92a4 0x92a4
%define program_environ 0x7b43
%define program_errno 0x7b1c
%define program_dos_error 0x7b27
%define program_batch_prefix 0x5e14
%define program_fallback_environment 0x9062
%define program_heap_mode 0x7b54
%define program_state_7b52 0x7b52
%define program_state_7b29 0x7b29
%define program_state_7b2a 0x7b2a
%define program_state_e462 0xe462
%define program_state_e45e 0xe45e
%define program_state_e460 0xe460
%define program_state_7b2b 0x7b2b
%define program_state_7b00 0x7b00
%endif
%include "encodings.inc"
program_environment_tail:
L_65ca: push bp
L_65cb: mov_load bp,sp
L_65cd: sub sp,0xe
L_65d0: push di
L_65d1: push si
L_65d2: sub_load di,di
L_65d4: cmp [bp+0x6],di
L_65d7: jnz short L_65df
L_65d9: mov ax,[program_environ]
L_65dc: mov [bp+0x6],ax
L_65df: cmp [bp+0x6],di
L_65e2: jz short L_6600
L_65e4: mov si,[bp+0x6]
L_65e7: cmp word [si],0x0
L_65ea: jz short L_6600
L_65ec: cmp di,0x7fff
L_65f0: ja short L_6600
L_65f2: inc si
L_65f3: inc si
L_65f4: push word [si-0x2]
L_65f7: call program_strlen
L_65fa: pop bx
L_65fb: inc ax
L_65fc: add_load di,ax
L_65fe: jmp short L_65e7
L_6600: cmp word [program_state_7b52],0x0
L_6605: jz short L_661c
L_6607: mov bx,[program_state_7b29]
L_660b: mov [bp-0x8],di
L_660e: or_load bx,bx
L_6610: jz short L_661e
L_6612: cmp byte [bx+program_state_7b2a],0x0
L_6617: jnz short L_661e
L_6619: dec bx
L_661a: jmp short L_660e
L_661c: sub_load bx,bx
L_661e: or_load bx,bx
L_6620: jz short L_6629
L_6622: lea ax,[bx+0x7]
L_6625: shl ax,1
L_6627: add_load di,ax
L_6629: mov [bp-0xa],bx
L_662c: cmp word [bp+0xe],0x0
L_6630: jz short L_663e
L_6632: push word [bp+0xe]
L_6635: call program_strlen
L_6638: pop bx
L_6639: add ax,strict word 0x3
L_663c: add_load di,ax
L_663e: lea ax,[di+0x1]
L_6641: mov [bp-0xe],ax
L_6644: cmp ax,0x7fff
L_6647: jna short L_6658
L_6649: mov word [program_errno],0x7
L_664f: mov word [program_dos_error],0xa
L_6655: jmp near L_66fe
L_6658: mov di,[program_heap_mode]
L_665c: mov word [program_heap_mode],0x10
L_6662: mov ax,[bp-0xe]
L_6665: add ax,strict word 0xf
L_6668: mov [program_state_e462],ax
L_666b: push ax
L_666c: call program_service_92a8
L_666f: pop bx
L_6670: mov_load si,ax
L_6672: or_load si,si
L_6674: jnz short L_66ac
L_6676: cmp word [program_state_e462],0x3aca
L_667c: ja short L_66ee
L_667e: push word [program_state_e462]
L_6682: call program_service_860f
L_6685: pop bx
L_6686: mov [program_state_e45e],ax
L_6689: mov [program_state_e460],dx
L_668d: mov_load ax,dx
L_668f: or ax,[program_state_e45e]
L_6693: jz short L_66ee
L_6695: push word [program_state_e462]
L_6699: push word [program_state_e45e]
L_669d: push dx
L_669e: mov si,program_fallback_environment
L_66a1: push si
L_66a2: call program_get_ds
L_66a5: push ax
L_66a6: call program_service_9286
L_66a9: add sp,0xa
L_66ac: mov [program_heap_mode],di
L_66b0: mov [bp-0xc],si
L_66b3: mov bx,[bp+0x8]
L_66b6: mov [bx],si
L_66b8: mov ax,[bp-0xc]
L_66bb: add ax,strict word 0xf
L_66be: and al,0xf0
L_66c0: mov_load si,ax
L_66c2: mov bx,[bp+0xa]
L_66c5: mov [bx],ax
L_66c7: cmp word [bp+0x6],0x0
L_66cb: jz short L_6704
L_66cd: mov di,[bp+0x6]
L_66d0: cmp word [di],0x0
L_66d3: jz short L_6704
L_66d5: sub_load ax,ax
L_66d7: push ax
L_66d8: inc di
L_66d9: inc di
L_66da: push word [di-0x2]
L_66dd: push si
L_66de: call program_strcpy
L_66e1: pop bx
L_66e2: pop bx
L_66e3: push ax
L_66e4: call program_strchr
L_66e7: pop bx
L_66e8: pop bx
L_66e9: inc ax
L_66ea: mov_load si,ax
L_66ec: jmp short L_66d0
L_66ee: mov word [program_errno],0xc
L_66f4: mov word [program_dos_error],0x8
L_66fa: mov [program_heap_mode],di
L_66fe: mov ax,0xffff
L_6701: jmp near L_6844
L_6704: cmp word [bp-0xa],0x0
L_6708: jz short L_6757
L_670a: sub_load ax,ax
L_670c: push ax
L_670d: mov ax,program_state_7b00
L_6710: push ax
L_6711: push si
L_6712: call program_strcpy
L_6715: pop bx
L_6716: pop bx
L_6717: push ax
L_6718: call program_strchr
L_671b: pop bx
L_671c: pop bx
L_671d: mov_load si,ax
L_671f: mov word [bp-0x8],0x0
L_6724: jmp short L_6748
L_6726: mov cl,0x4
L_6728: mov bx,[bp-0x8]
L_672b: mov al,[bx+program_state_7b2b]
L_672f: sar al,cl
L_6731: and al,0xf
L_6733: add al,0x41
L_6735: inc si
L_6736: mov [si-0x1],al
L_6739: mov al,[bx+program_state_7b2b]
L_673d: and al,0xf
L_673f: add al,0x41
L_6741: inc si
L_6742: mov [si-0x1],al
L_6745: inc word [bp-0x8]
L_6748: mov ax,[bp-0xa]
L_674b: dec word [bp-0xa]
L_674e: or_load ax,ax
L_6750: jnz short L_6726
L_6752: inc si
L_6753: mov byte [si-0x1],0x0
L_6757: inc si
L_6758: mov byte [si-0x1],0x0
L_675c: cmp word [bp+0xe],0x0
L_6760: jz short L_6775
L_6762: inc si
L_6763: mov byte [si-0x1],0x1
L_6767: inc si
L_6768: mov byte [si-0x1],0x0
L_676c: push word [bp+0xe]
L_676f: push si
L_6770: call program_strcpy
L_6773: pop bx
L_6774: pop bx
L_6775: sub_load di,di
L_6777: mov si,[bp+0xc]
L_677a: inc si
L_677b: cmp [bp+0x10],di
L_677e: jz short L_67b0
L_6780: sub_load ax,ax
L_6782: push ax
L_6783: push word [bp+0x10]
L_6786: push ax
L_6787: mov ax,program_batch_prefix
L_678a: push ax
L_678b: push si
L_678c: call program_strcpy
L_678f: pop bx
L_6790: pop bx
L_6791: push ax
L_6792: call program_strchr
L_6795: pop bx
L_6796: pop bx
L_6797: mov_load si,ax
L_6799: push si
L_679a: call program_strcpy
L_679d: pop bx
L_679e: pop bx
L_679f: push ax
L_67a0: call program_strchr
L_67a3: pop bx
L_67a4: pop bx
L_67a5: sub ax,strict word 0x4
L_67a8: mov_load si,ax
L_67aa: mov_load di,ax
L_67ac: sub di,[bp+0xc]
L_67af: dec di
L_67b0: mov bx,[bp+0x4]
L_67b3: cmp word [bx],0x0
L_67b6: jz short L_6837
L_67b8: cmp word [bx+0x2],0x0
L_67bc: jz short L_67c4
L_67be: inc si
L_67bf: mov byte [si-0x1],0x20
L_67c3: inc di
L_67c4: mov [bp-0x6],si
L_67c7: mov ax,[bp+0x4]
L_67ca: inc ax
L_67cb: inc ax
L_67cc: mov [bp-0x2],ax
L_67cf: jmp short L_6812
L_67d1: push word [bx]
L_67d3: call program_strlen
L_67d6: pop bx
L_67d7: mov [bp-0x4],ax
L_67da: add_load ax,di
L_67dc: cmp ax,strict word 0x7d
L_67df: ja short L_681f
L_67e1: add di,[bp-0x4]
L_67e4: sub_load ax,ax
L_67e6: push ax
L_67e7: mov bx,[bp-0x2]
L_67ea: add word [bp-0x2],0x2
L_67ee: push word [bx]
L_67f0: push word [bp-0x6]
L_67f3: call program_strcpy
L_67f6: pop bx
L_67f7: pop bx
L_67f8: push ax
L_67f9: call program_strchr
L_67fc: pop bx
L_67fd: pop bx
L_67fe: mov [bp-0x6],ax
L_6801: mov bx,[bp-0x2]
L_6804: cmp word [bx],0x0
L_6807: jz short L_6812
L_6809: mov_load bx,ax
L_680b: inc word [bp-0x6]
L_680e: mov byte [bx],0x20
L_6811: inc di
L_6812: mov bx,[bp-0x2]
L_6815: cmp word [bx],0x0
L_6818: jnz short L_67d1
L_681a: mov si,[bp-0x6]
L_681d: jmp short L_6837
L_681f: mov word [program_errno],0x7
L_6825: mov word [program_dos_error],0xa
L_682b: mov bx,[bp+0x8]
L_682e: push word [bx]
L_6830: call program_service_92a4
L_6833: pop bx
L_6834: jmp near L_66fe
L_6837: mov byte [si],0xd
L_683a: mov_load ax,di
L_683c: mov bx,[bp+0xc]
L_683f: mov [bx],al
L_6841: mov ax,[bp-0xe]
L_6844: pop si
L_6845: pop di
L_6846: mov_load sp,bp
L_6848: pop bp
L_6849: ret
