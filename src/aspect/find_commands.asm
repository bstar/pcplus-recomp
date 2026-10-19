; PCPlus2.01 native FIND command and string-search services, DS=SS/DF=0.
; Original SHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Resident4FB4..4FF6,9146..91A6,9764..9786; overlay04 DCDB..DD28.
; REA ev_a8e6f63aa7559b03f5f26fa46b77410207bd2a79f0894e44b77adb78d8ece4aa,
; ev_8b7826f70682441f851a1f58459a2c6d7dd382a94726aae85553b35b0d78e7bc,
; ev_1d1b0693dbd5f3d63692385c2e48c78594874e352426a5b6f585328dcc12bd64.
; RET entries; helpers cdecl near pointers/resultAX, caller cleanup.
; Insensitive search duplicates both inputs in a NEAR allocator and frees both.
; Its native allocation-failure dereference remains unchecked. Do not substitute
; a far allocator or claim null-safe rollback. Nonmatch optional index stores
; wrapped(0-sourcepointer), not -1. FOUND is shared native E39C.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FIND_FLAT
%if ASPECT_FIND_UNIT=1
ORG 0x4fb4
%elif ASPECT_FIND_UNIT=2
ORG 0x9146
%elif ASPECT_FIND_UNIT=3
ORG 0xdcdb
%elif ASPECT_FIND_UNIT=4
ORG 0x9764
%else
%error Select ASPECT_FIND_UNIT1..4
%endif
%define aspect_string_read 0xce1f
%define aspect_string_option_flag 0xcd5f
%define aspect_expr_integer_destination 0xce13
%define aspect_set_findcase_value 0xe392
%define aspect_find_found 0xe39c
%define aspect_find_upper 0x9128
%define aspect_find_alloc 0x92a8
%define aspect_find_free 0x92a4
%define program_strcpy 0x8268
%define aspect_string_strlen 0x8d18
%if ASPECT_FIND_UNIT!=1
%define aspect_find_command 0x4fb4
%endif
%if ASPECT_FIND_UNIT!=2
%define aspect_find_sensitive 0x9146
%endif
%if ASPECT_FIND_UNIT!=3
; Resident command calls the overlay04 thunk, not its loaded body.
%define aspect_find_insensitive 0xcdef
%endif
%if ASPECT_FIND_UNIT!=4
%define aspect_find_duplicate 0x9764
%endif
%else
%define ASPECT_FIND_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_find_command,aspect_find_sensitive,aspect_find_insensitive,aspect_find_duplicate
extern aspect_string_read,aspect_string_option_flag,aspect_expr_integer_destination
extern aspect_set_findcase_value,aspect_find_found
extern aspect_find_upper,aspect_find_alloc,aspect_find_free
extern program_strcpy,aspect_string_strlen
%endif
%if ASPECT_FIND_UNIT=0 || ASPECT_FIND_UNIT=1
aspect_find_command:
 push di
 push si
 call aspect_string_read
 mov_load si,ax
 cmp word [aspect_set_findcase_value],byte 0
 jnz .sensitive
 call aspect_string_read
 push ax
 push si
 call aspect_find_insensitive
 jmp short .searched
.sensitive:
 call aspect_string_read
 push ax
 push si
 call aspect_find_sensitive
.searched:
 pop bx
 pop bx
 mov_load di,ax
 call aspect_string_option_flag
 or_load ax,ax
 jz .status
 call aspect_expr_integer_destination
 mov_load bx,ax
 mov_load ax,di
 sub_load ax,si
 mov [bx],ax
.status:
 cmp di,byte 1
 sbb_load ax,ax
 inc ax
 mov [aspect_find_found],ax
 pop si
 pop di
 ret
%endif
%if ASPECT_FIND_UNIT=0 || ASPECT_FIND_UNIT=2
aspect_find_sensitive:
 push bp
 mov_load bp,sp
 sub sp,byte 2
 push si
 push di
 push ds
 pop es
 mov di,[bp+6]
 xor_load ax,ax
 mov cx,0xffff
 repne scasb
 not cx
 dec cx
 jcxz .empty
 dec cx
 mov [bp-2],cx
 mov di,[bp+4]
 mov_load bx,di
 xor_load ax,ax
 mov cx,0xffff
 repne scasb
 not cx
 dec cx
 mov_load dx,cx
 sub dx,[bp-2]
 jbe .absent
 mov_load di,bx
.next:
 mov si,[bp+6]
 lodsb
 mov_load di,bx
 mov_load cx,dx
 repne scasb
 jnz .absent
 mov_load dx,cx
 mov_load bx,di
 mov cx,[bp-2]
 jcxz .found
 repe cmpsb
 jnz .next
.found:
 lea ax,[bx-1]
 jmp short .done
.empty:
 mov ax,[bp+4]
 jmp short .done
.absent:
 xor_load ax,ax
.done:
 pop di
 pop si
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FIND_UNIT=0 || ASPECT_FIND_UNIT=3
aspect_find_insensitive:
 push bp
 mov_load bp,sp
 sub sp,byte 2
 push di
 push si
 push word [bp+4]
 call aspect_find_duplicate
 pop bx
 mov_load si,ax
 push word [bp+6]
 call aspect_find_duplicate
 pop bx
 mov_load di,ax
 push si
 call aspect_find_upper
 pop bx
 push di
 call aspect_find_upper
 pop bx
 push di
 push si
 call aspect_find_sensitive
 pop bx
 pop bx
 mov [bp-2],ax
 or_load ax,ax
 jz .release
 mov ax,[bp+4]
 sub_load ax,si
 add [bp-2],ax
.release:
 push si
 call aspect_find_free
 pop bx
 push di
 call aspect_find_free
 pop bx
 mov ax,[bp-2]
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FIND_UNIT=0 || ASPECT_FIND_UNIT=4
aspect_find_duplicate:
 push bp
 mov_load bp,sp
 push di
 mov di,[bp+4]
 push di
 call aspect_string_strlen
 inc ax
 push ax
 call aspect_find_alloc
 pop bx
 or_load ax,ax
 jnz .copy
 pop bx
 jmp short .done
.copy:
 push ax
 call program_strcpy
 add sp,byte 4
.done:
 pop di
 pop bp
 ret
%endif
