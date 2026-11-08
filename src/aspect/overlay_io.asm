; Maintained DOS I/O adapter for the Open Watcom standard overlay manager.
; The public interface is bld/wl/ovlldr/h/ovlstd.h in the pinned toolchain.
; This adapter requires an exact read count before accepting executable code
; or relocation records. The initial far-data preload may end at BSS, but
; only after all initialized bytes through linker _edata have been read.
; It uses the existing loader's fatal I/O-error path;
; no partial overlay may be entered and no error is silently retried.
; Open: DX:AX name. Seek: AX handle, CX:BX position. Read: AX handle,
; CX:BX far buffer, DX length. tiny_ret_t returns DX:AX, negative on error.
; Preserve the library interface's SI/DS and Open's BX/CX, Close's BX/DX.
BITS 16
CPU 8086
SEGMENT _TEXT public align=4 class=_OVLCODE use16
extern ___OVLFLAGS__,___OVLSHARE__
extern _runtime_get_field_storage,_edata
global __OvlOpen___,__OvlSeek___,__OvlRead___,__OvlClose___
__OvlOpen___:
 push bx
 push cx
 push ds
 mov cx,dx
 mov dx,ax
 mov ds,cx
 mov al,[cs:___OVLSHARE__]
 test byte [cs:___OVLFLAGS__],2
 jz .mode
 or al,0x80                    ; DOS3+: do not inherit the loader handle
.mode:
 mov ah,0x3d
 int 0x21
 sbb dx,dx
 pop ds
 pop cx
 pop bx
 ret
__OvlSeek___:
 xchg ax,bx                    ; BX handle, AX low position
 mov dx,ax
 mov ax,0x4200
 int 0x21
 jc .error
 and dx,0x7fff
 ret
.error:
 or dx,0x8000
 ret
__OvlRead___:
 push si
 push ds
 mov ds,cx
 mov si,dx                     ; retain requested bytes across DOS
 xchg ax,bx
 mov dx,ax
 mov cx,si
 mov ah,0x3f
 int 0x21
 jc .error
 cmp ax,si
 jne .short
 xor dx,dx
 jmp short .done
.short:
 ; Watcom preloads the far field state and DGROUP in one request including
 ; BSS/stack bytes that need not exist on disk. Preserve that startup format,
 ; while refusing a missing initialized prefix. This segment cannot contain
 ; any of the replaceable code banks or loader relocation scratch space.
 mov bx,ds
 mov cx,seg _runtime_get_field_storage
 cmp bx,cx
 jne .short_error
 or dx,dx
 jnz .short_error
 mov cx,seg _edata
 sub cx,bx
 jc .short_error
 cmp cx,0x1000
 jae .short_error
 mov bx,cx
 mov cl,4
 shl bx,cl
 add bx,_edata
 jc .short_error
 cmp ax,bx
 jb .short_error
 xor dx,dx
 jmp short .done
.short_error:
 mov ax,5                      ; refuse an incomplete code/relocation read
.error:
 mov dx,0xffff
.done:
 pop ds
 pop si
 ret
__OvlClose___:
 push bx
 push dx
 mov bx,ax
 mov ah,0x3e
 int 0x21
 pop dx
 pop bx
 ret
