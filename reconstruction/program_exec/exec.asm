; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_exec
%ifdef PROGRAM_NOTICE_DIAGNOSTIC
extern _notice_fault_exec_count,_notice_fault_exec_mode
%endif
extern program_exec_result
extern program_saved_sp
extern program_saved_ss
extern program_saved_pair_low
extern program_saved_pair_high
extern program_saved_ds
extern program_pair_low
extern program_errno
extern program_exec_block
extern program_exec_tail
extern program_exec_tail_segment
extern program_exec_fcb1_segment
extern program_exec_fcb2_segment
extern program_fcb1
extern program_fcb2
extern program_exec_active
extern program_overlay_gate
extern program_overlay_callback
%define short
%else
ORG 0x6a22
%define program_exec_result 0x9435
%define program_saved_sp 0x6a18
%define program_saved_ss 0x6a1a
%define program_saved_pair_low 0x6a1c
%define program_saved_pair_high 0x6a1e
%define program_saved_ds 0x6a20
%define program_pair_low 0x2e
%define program_errno 0x7b1c
%define program_exec_block 0x5e36
%define program_exec_tail 0x5e38
%define program_exec_tail_segment 0x5e3a
%define program_exec_fcb1_segment 0x5e3e
%define program_exec_fcb2_segment 0x5e42
%define program_fcb1 0x5e44
%define program_fcb2 0x5e54
%define program_exec_active 0x7b4a
%define program_overlay_gate 0x8e24
%define program_overlay_callback 0x8e26
%endif
%include "encodings.inc"
program_exec:
L_6a22: push bp
L_6a23: mov_load bp,sp
L_6a25: cmp word [bp+0x4],0x1
L_6a29: jz short L_6a3e
L_6a2b: cmp word [bp+0x4],0x0
L_6a2f: jz short L_6a3e
L_6a31: mov word [program_errno],0x16
L_6a37: mov ax,0xffff
L_6a3a: clc
L_6a3b: jmp near program_exec_result
L_6a3e: push si
L_6a3f: push di
L_6a40: mov ax,ds
L_6a42: mov bx,[bp+0xa]
L_6a45: mov cl,0x4
L_6a47: shr bx,cl
L_6a49: add_load ax,bx
L_6a4b: mov [program_exec_block],ax
L_6a4e: mov ax,[bp+0x8]
L_6a51: mov [program_exec_tail],ax
L_6a54: mov word [program_exec_tail_segment],ds
L_6a58: mov word [program_exec_fcb1_segment],ds
L_6a5c: mov word [program_exec_fcb2_segment],ds
L_6a60: push ds
L_6a61: pop es
L_6a62: mov si,[program_exec_tail]
L_6a66: inc si
L_6a67: mov di,program_fcb1
L_6a6a: mov ax,0x2901
L_6a6d: int byte 0x21
L_6a6f: mov ax,0x2901
L_6a72: mov di,program_fcb2
L_6a75: int byte 0x21
L_6a77: cmp word [program_overlay_gate],0xd6d6
L_6a7d: jnz short L_6a86
L_6a7f: mov bx,0xffff
L_6a82: call word near [program_overlay_callback]
L_6a86: push bp
L_6a87: push es
L_6a88: push ds
L_6a89: mov word [cs:program_saved_ss],ss
L_6a8e: mov [cs:program_saved_sp],sp
L_6a93: mov di,program_pair_low
L_6a96: mov si,[di]
L_6a98: mov [cs:program_saved_pair_low],si
L_6a9d: mov si,[di+0x2]
L_6aa0: mov [cs:program_saved_pair_high],si
L_6aa5: mov word [cs:program_saved_ds],ds
L_6aaa: mov bx,program_exec_block
L_6aad: cmp word [bp+0x4],0x0
L_6ab1: jz short L_6ab9
L_6ab3: mov al,0x4
L_6ab5: xor_load cx,cx
L_6ab7: jmp short L_6abb
L_6ab9: xor_load al,al
L_6abb: clc
L_6abc: push ax
L_6abd: mov ah,0xb
L_6abf: int byte 0x21
L_6ac1: pop ax
L_6ac2: mov word [program_exec_active],0x1
L_6ac8: mov dx,[bp+0x6]
L_6acb: mov ah,0x4b
%ifdef PROGRAM_NOTICE_DIAGNOSTIC
 ; Diagnostic-only witness immediately before the actual DOS call. Preserve
 ; FLAGS and all registers; the flat and ordinary OMF products are unchanged.
 pushf
 inc word [_notice_fault_exec_count]
 ; Explicit unsupported-mode fixture requests real DOS error11. It does not
 ; pretend to establish malformed-MZ rejection by the built-in DOS loader.
 or al,byte [_notice_fault_exec_mode]
 popf
%endif
L_6acd: int byte 0x21
L_6acf: xchg ax,bx
L_6ad0: lahf
L_6ad1: cli
L_6ad2: mov ss,word [cs:program_saved_ss]
L_6ad7: mov sp,[cs:program_saved_sp]
L_6adc: sti
L_6add: mov di,program_pair_low
L_6ae0: mov ds,word [cs:program_saved_ds]
L_6ae5: mov si,[cs:program_saved_pair_high]
L_6aea: mov [di+0x2],si
L_6aed: mov si,[cs:program_saved_pair_low]
L_6af2: mov [di],si
L_6af4: sahf
L_6af5: xchg ax,bx
L_6af6: pop ds
L_6af7: mov word [program_exec_active],0x0
L_6afd: pop es
L_6afe: pop bp
L_6aff: pop di
L_6b00: pop si
L_6b01: jc short L_6b07
L_6b03: mov ah,0x4d
L_6b05: int byte 0x21
L_6b07: jmp near program_exec_result
