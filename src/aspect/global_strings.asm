; Exact PCPlus2.01 overlay2 D850..D8B4 global-string lifecycle.
; Retained REA assembly evidence:
; D850 ev_dbc3bcf3bb931cbd0cf28570a05d5156f682cfe62da94105e834a75d5fe3e749
; D88E ev_a2d880c716be2a76af6e9fe26d4135d05a4ab84aafe2d8240d904763b09c7a53
; Original SHA256 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Source: analysis/pcplus-overlay-anchored-02/functions/0x1d850.asm and0x1d88e.asm.
; Near entry/return, DS=SS, preserves SI/DI; ES and AX/BX/CX/DX/flags volatile.
; read returns AX; alloc(81), caller-cleaned, returns far pointer DX:AX;
; free(offset,segment) is caller-cleaned; error(101) consumes its argument if
; it returns. Real error handling can longjmp out, so no rollback is implied.
; Native code stores the complete read word and uses signed JG without bounds.
; Valid compiler counts are0..128. Malformed higher counts can overwrite the
; table; negative values skip loops. Release does not clear pointers or count.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_GLOBALS_FLAT
ORG 0xd850
%define aspect_globals_read 0x4cb4
%define aspect_globals_alloc 0x860f
%define aspect_globals_error 0x4efb
%define aspect_globals_free 0x85fc
%define aspect_globals_count 0xe3be
%define aspect_globals_table 0xdb82
%else
SEGMENT _TEXT public class=CODE use16
global aspect_globals_initialize,aspect_globals_release
extern aspect_globals_read,aspect_globals_alloc,aspect_globals_error,aspect_globals_free
extern aspect_globals_count,aspect_globals_table
%endif
aspect_globals_initialize:
 push di
 push si
 call aspect_globals_read
 mov [aspect_globals_count],ax
 sub_load di,di
 mov si,aspect_globals_table
 jmp short .test
.allocate:
 mov ax,81
 push ax
 call aspect_globals_alloc
 pop bx
 mov [si],ax
 mov [si+2],dx
 mov_load ax,dx
 or ax,[si]
 jz .failed
 les bx,[si]
 mov byte [es:bx],0
 jmp short .next
.failed:
 mov ax,101
 push ax
 call aspect_globals_error
.next:
 add si,byte 4
 inc di
.test:
 cmp [aspect_globals_count],di
 jg .allocate
 pop si
 pop di
 ret
aspect_globals_release:
 push di
 push si
 sub_load di,di
 mov si,aspect_globals_table
 jmp short .test
.release:
 mov ax,[si+2]
 or ax,[si]
 jz .next
 push word [si+2]
 push word [si]
 call aspect_globals_free
 pop bx
 pop bx
.next:
 add si,byte 4
 inc di
.test:
 cmp [aspect_globals_count],di
 jg .release
 pop si
 pop di
 ret
