; Exact compact retained form of the native ASPECT REDIAL selection list.
;
; Native layout (overlay 5, DS:70B4): fifteen 7-byte slots. Bytes 0..4 hold the
; strncpy(slot,token,5) text, byte 5 is always 0 and byte 6 is the consumed
; flag (0 or 1). No native writer produces another byte-5/flag value, so the
; reachable state is exactly 15*5 token bytes plus 15 flag bits.
;
; Retained layout (77 bytes): the fifteen 5-byte token fields, then a WORD
; mask whose bit i is slot i's flag. Bit 15 is always 0. The initial value is
; the native DGROUP initial state: every slot empty with the flag set.
;
; This codec belongs to the transient PCCONN image (its own _TEXT): the
; module unpacks the parent's retained owner (src/terminal/
; redial_selection_storage.asm) into its native DS:70B4 area on entry and
; packs it back on every exit path, so only the 80-byte owner stays resident.
;
; redial_selection_pack   DS:SI -> native 105, ES:DI -> retained 77
; redial_selection_unpack DS:SI -> retained 77, ES:DI -> native 105
; Both are near, need DF=0 (set here), preserve SI/DI/BP/DS/ES and clobber
; AX/BX/CX/DX. CF=1 rejects an unreachable state and leaves ES:DI unchanged.
; Token bytes after a NUL are copied verbatim, so every reachable native
; state round-trips byte for byte.
BITS 16
CPU 8086
%ifdef REDIAL_SELECTION_FLAT
; Flat check image: offsets of pack and unpack.
 dw redial_selection_pack,redial_selection_unpack
%else
SEGMENT _TEXT public class=CODE use16
global redial_selection_pack,redial_selection_unpack
%endif

REDIAL_SLOTS equ 15
REDIAL_NATIVE_SLOT equ 7
REDIAL_TOKEN equ 5
REDIAL_MASK_OFFSET equ REDIAL_SLOTS*REDIAL_TOKEN
REDIAL_RETAINED_SIZE equ REDIAL_MASK_OFFSET+2

redial_selection_pack:
 push si
 push di
 push si
 mov cx,REDIAL_SLOTS
 xor bx,bx
 mov dx,1
.validate:
 cmp byte [si+REDIAL_TOKEN],0
 jne .reject
 mov al,[si+REDIAL_TOKEN+1]
 cmp al,1
 ja .reject
 jb .next_flag
 or bx,dx
.next_flag:
 shl dx,1
 add si,REDIAL_NATIVE_SLOT
 loop .validate
 pop si
 cld
 mov cx,REDIAL_SLOTS
.copy:
 movsw
 movsw
 movsb
 inc si
 inc si
 loop .copy
 mov ax,bx
 stosw
 pop di
 pop si
 clc
 ret
.reject:
 pop si
 pop di
 pop si
 stc
 ret

redial_selection_unpack:
 push si
 push di
 mov bx,[si+REDIAL_MASK_OFFSET]
 test bh,0x80
 jnz .reject
 cld
 mov cx,REDIAL_SLOTS
.copy:
 movsw
 movsw
 movsb
 xor al,al
 stosb
 shr bx,1
 adc al,0
 stosb
 loop .copy
 pop di
 pop si
 clc
 ret
.reject:
 pop di
 pop si
 stc
 ret
