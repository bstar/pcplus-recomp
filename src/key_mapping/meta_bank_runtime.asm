; Production bank bindings. Existing CONFIG callbacks supply near CRT and
; canonical paths; Meta adds44 resident service bytes and no DGROUP data.
BITS 16
CPU 8086
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
GROUP META_EDITOR_GROUP META_EDITOR_CODE
%macro crt 1
global meta_bank_%1_
extern config_%1_service__resident
meta_bank_%1_:
 push es
 call far config_%1_service__resident
 pop es
 ret
%endmacro
crt memcpy
crt memset
crt memcmp
crt strchr
crt strcmp
crt strlen
; Explicit far memory primitives implement the generic Watcom register ABI.
; AX:offset/DX:segment, BX:offset/CX:segment for the second far pointer.
; memcpy/memcmp's fifth word is caller stack count, removed with RET2.
; Preserve DS,ES,SI,DI,BP and retain DS=SS on return. DF is clear as C requires.
global meta_bank_fmemcpy_,meta_bank_fmemset_,meta_bank_fmemcmp_,meta_bank_fstrcmp_
meta_bank_fmemcpy_:
 push bp
 mov bp,sp
 push ax
 push si
 push di
 push ds
 push es
 mov di,ax
 mov es,dx
 mov si,bx
 mov ds,cx
 mov cx,[bp+4]
 cld
 rep movsb
 pop es
 pop ds
 pop di
 pop si
 pop ax
 pop bp
 ret 2
meta_bank_fmemset_:
 push ax
 push di
 push es
 mov di,ax
 mov es,dx
 mov al,bl
 cld
 rep stosb
 pop es
 pop di
 pop ax
 ret
meta_bank_fmemcmp_:
 push bp
 mov bp,sp
 push si
 push di
 push ds
 push es
 mov si,ax
 mov ds,dx
 mov di,bx
 mov es,cx
 mov cx,[bp+4]
 xor ax,ax
 jcxz .done
 cld
 repe cmpsb
 je .done
 sbb ax,ax
 or ax,1
.done:
 pop es
 pop ds
 pop di
 pop si
 pop bp
 ret 2
meta_bank_fstrcmp_:
 push si
 push di
 push ds
 push es
 mov si,ax
 mov ds,dx
 mov di,bx
 mov es,cx
 cld
.loop:
 lodsb
 cmp al,[es:di]
 jne .different
 inc di
 or al,al
 jnz .loop
 xor ax,ax
 jmp short .done
.different:
 sbb ax,ax
 or ax,1
.done:
 pop es
 pop ds
 pop di
 pop si
 ret
; These two parent helpers use register arguments, whereas the bank's caller
; supplies two cdecl near pointers. Preserve the caller's slots and ES.
%macro fs 2
global _meta_bank_%1
extern %2
_meta_bank_%1:
 push bp
 mov bp,sp
 push es
 mov ax,[bp+4]
 mov dx,[bp+6]
 call far %2
 pop es
 pop bp
 ret
%endmacro
fs canonical,config_canonical_service__resident
fs attributes,meta_bank_attributes_service__resident
; Existing cdecl callbacks already expect the near thunk return followed by
; their far return before the original arguments, so no extra frame is added.
global _meta_bank_paths,_meta_bank_actions,_meta_bank_resource
extern _meta_bank_paths_resident,_meta_bank_actions_resident
extern _meta_bank_resource_resident
_meta_bank_paths:
 call far _meta_bank_paths_resident
 ret
_meta_bank_actions:
 call far _meta_bank_actions_resident
 ret
_meta_bank_resource:
 call far _meta_bank_resource_resident
 ret
